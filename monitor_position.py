#!/usr/bin/env python3
"""
SkyScreen for macOS
Detects external monitor connections and allows positioning with Cmd + Arrow keys
"""

import rumps
import threading
import time
import tempfile
import os
from pynput import keyboard
from Quartz import (
    CGDisplayIsActive,
    CGDisplayIsBuiltin,
    CGGetActiveDisplayList,
    CGDisplayBounds,
    CGConfigureDisplayOrigin,
    CGBeginDisplayConfiguration,
    CGCompleteDisplayConfiguration,
    kCGConfigureForSession
)
from PIL import Image, ImageDraw, ImageFont


class MonitorPositioner(rumps.App):
    def __init__(self):
        super(MonitorPositioner, self).__init__("", quit_button=None)
        
        self.menu = ["Activate Positioning", None, "Quit"]
        
        self.activation_window_active = False
        self.activation_timer = None
        self.keyboard_listener = None
        self.cmd_pressed = False
        self.arrows_pressed = set()
        self.blink_timer = None
        self.blink_state = False
        
        self.current_displays = set()
        self.external_displays = []  # Queue of external displays to position
        self.positioned_externals = []  # List of already positioned external displays
        self.current_external_id = None  # The external display being positioned now
        self.reference_display_id = None  # The display to position relative to
        self.main_display_id = None
        
        self.default_icon = self.create_icon_image("●", inactive=True)
        self.blank_icon = self.create_icon_image("")
        self.active_icon = self.create_icon_image("●", inactive=False)
        self.up_icon = self.create_icon_image("↑")
        self.down_icon = self.create_icon_image("↓")
        self.left_icon = self.create_icon_image("←")
        self.right_icon = self.create_icon_image("→")
        self.blocked_up_icon = self.create_icon_image("↑", blocked=True)
        self.blocked_down_icon = self.create_icon_image("↓", blocked=True)
        self.blocked_left_icon = self.create_icon_image("←", blocked=True)
        self.blocked_right_icon = self.create_icon_image("→", blocked=True)
        self.top_left_icon = self.create_icon_image("↖")
        self.top_right_icon = self.create_icon_image("↗")
        self.bottom_left_icon = self.create_icon_image("↙")
        self.bottom_right_icon = self.create_icon_image("↘")
        self.blocked_top_left_icon = self.create_icon_image("↖", blocked=True)
        self.blocked_top_right_icon = self.create_icon_image("↗", blocked=True)
        self.blocked_bottom_left_icon = self.create_icon_image("↙", blocked=True)
        self.blocked_bottom_right_icon = self.create_icon_image("↘", blocked=True)
        
        self.icon = self.default_icon
        
        self.monitor_thread = threading.Thread(target=self.monitor_displays, daemon=True)
        self.monitor_thread.start()
    
    def create_icon_image(self, symbol, inactive=False, blocked=False):
        """Create a menu bar icon with the given symbol and save to temp file"""
        img = Image.new('RGBA', (44, 44), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # For all symbols, use text
        font = None
        font_paths = [
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial Unicode.ttf"
        ]
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 42)
                break
            except Exception as e:
                print(f"Failed to load font {font_path}: {e}")
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        # Use red for blocked, darker gray for inactive, white for active
        if blocked:
            color = (255, 0, 0, 255)  # Red for blocked
        elif inactive:
            color = (128, 128, 128, 255)  # Darker gray
        else:
            color = (255, 255, 255, 255)  # White
        
        draw.text((22, 22), symbol, fill=color, anchor="mm", font=font)
        
        if blocked and symbol in ["↖", "↗", "↙", "↘"]:
            draw.line([(8, 8), (36, 36)], fill=(255, 0, 0, 255), width=3)
        
        if blocked and symbol in ["↑", "↓", "←", "→"]:
            draw.line([(8, 22), (36, 22)], fill=(255, 0, 0, 255), width=3)
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        img.save(temp_file.name, format='PNG')
        temp_file.close()
        
        return temp_file.name
    
    def get_displays(self):
        """Get all active displays"""
        max_displays = 16
        (err, active_displays, num_displays) = CGGetActiveDisplayList(max_displays, None, None)
        if err:
            return []
        return active_displays[:num_displays]
    
    def get_all_external_displays(self):
        """Get all external displays (non-built-in)"""
        displays = self.get_displays()
        externals = []
        for display_id in displays:
            if not CGDisplayIsBuiltin(display_id):
                externals.append(display_id)
        return externals
    
    def get_main_display(self):
        """Find the main built-in display"""
        displays = self.get_displays()
        for display_id in displays:
            if CGDisplayIsBuiltin(display_id):
                return display_id
        return displays[0] if displays else None
    
    def monitor_displays(self):
        """Monitor for new display connections"""
        while True:
            current = set(self.get_displays())
            
            # Clean up disconnected displays from our tracking lists
            if len(current) < len(self.current_displays):
                # Displays were disconnected
                disconnected = self.current_displays - current
                
                # Remove from positioned externals
                self.positioned_externals = [d for d in self.positioned_externals if d not in disconnected]
                
                # Remove from queue
                self.external_displays = [d for d in self.external_displays if d not in disconnected]
                
                # Clear current if it was disconnected
                if self.current_external_id in disconnected:
                    self.current_external_id = None
                    self.deactivate_positioning_mode()
                
                print(f"Detected {len(disconnected)} display(s) disconnected. Cleaned up tracking.")
            
            if current != self.current_displays and len(current) > len(self.current_displays):
                # New display detected
                all_externals = self.get_all_external_displays()
                
                # Exclude displays that are already positioned, in the queue, or currently being positioned
                new_externals = [
                    d for d in all_externals 
                    if d not in self.positioned_externals 
                    and d not in self.external_displays
                    and d != self.current_external_id
                ]
                
                if new_externals:
                    # Add new external displays to the queue
                    self.external_displays.extend(new_externals)
                    print(f"Detected {len(new_externals)} new external display(s). Added to positioning queue.")
                    
                    # Set main display if not set
                    if not self.main_display_id:
                        self.main_display_id = self.get_main_display()
                    
                    # If not currently positioning, start positioning the next monitor
                    if not self.activation_window_active and self.external_displays:
                        self.start_next_positioning()
            
            self.current_displays = current
            time.sleep(2)
    
    def start_next_positioning(self):
        """Start positioning the next external monitor in the queue"""
        if not self.external_displays:
            print("No more monitors to position")
            # Clear state when done
            self.current_external_id = None
            self.reference_display_id = None
            return
        
        # If already in an activation window, deactivate it first to reset the timer
        if self.activation_window_active:
            self.deactivate_positioning_mode()
        
        # Get the next monitor to position
        self.current_external_id = self.external_displays.pop(0)
        
        self.reference_display_id = self.main_display_id
        monitor_num = len(self.positioned_externals) + 1
        print(f"Positioning external monitor #{monitor_num} (relative to main display)")
        
        self.activate_positioning_mode()
    
    def activate_positioning_mode(self):
        """Activate 30-second window for positioning"""
        if self.activation_window_active:
            return
        
        self.activation_window_active = True
        self.cmd_pressed = False
        self.arrows_pressed.clear()
        
        # Start blinking icon
        self.start_blinking()
        
        try:
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.keyboard_listener.start()
        except Exception as e:
            print(f"Keyboard listener failed (needs accessibility permissions): {e}")
            print("Menu bar icon should still be visible. Grant accessibility permissions to enable keyboard shortcuts.")
        
        self.activation_timer = threading.Timer(30.0, self.deactivate_positioning_mode)
        self.activation_timer.start()
    
    def start_blinking(self):
        """Start blinking the icon"""
        self.blink_state = True
        self.blink()
    
    def blink(self):
        """Toggle icon visibility for blinking effect"""
        if not self.activation_window_active:
            return
        
        if self.blink_state:
            self.icon = self.blank_icon
        else:
            self.icon = self.active_icon
        
        self.blink_state = not self.blink_state
        
        # Continue blinking every 0.5 seconds
        self.blink_timer = threading.Timer(0.5, self.blink)
        self.blink_timer.start()
    
    def stop_blinking(self):
        """Stop blinking effect"""
        if self.blink_timer:
            self.blink_timer.cancel()
            self.blink_timer = None
    
    def deactivate_positioning_mode(self):
        """Deactivate positioning mode"""
        self.activation_window_active = False
        
        # Stop blinking
        self.stop_blinking()
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        
        if self.activation_timer:
            self.activation_timer.cancel()
            self.activation_timer = None
        
        # Reset to darker inactive icon when positioning window closes
        self.icon = self.default_icon
        
        # Clear state if no more monitors to position
        if not self.external_displays:
            self.current_external_id = None
            self.reference_display_id = None
        
        print("Positioning window closed. Icon reset to inactive (darker ●)")
    
    def on_key_press(self, key):
        """Handle keyboard input during activation window"""
        if not self.activation_window_active:
            return
        
        if key == keyboard.Key.cmd or key == keyboard.Key.cmd_r:
            self.cmd_pressed = True
            return
        
        if key in (keyboard.Key.up, keyboard.Key.down, keyboard.Key.left, keyboard.Key.right):
            self.arrows_pressed.add(key)
        
        if not self.cmd_pressed:
            return
        
        direction = None
        
        if keyboard.Key.up in self.arrows_pressed and keyboard.Key.left in self.arrows_pressed:
            direction = 'top_left'
        elif keyboard.Key.up in self.arrows_pressed and keyboard.Key.right in self.arrows_pressed:
            direction = 'top_right'
        elif keyboard.Key.down in self.arrows_pressed and keyboard.Key.left in self.arrows_pressed:
            direction = 'bottom_left'
        elif keyboard.Key.down in self.arrows_pressed and keyboard.Key.right in self.arrows_pressed:
            direction = 'bottom_right'
        elif key == keyboard.Key.up:
            direction = 'up'
        elif key == keyboard.Key.down:
            direction = 'down'
        elif key == keyboard.Key.left:
            direction = 'left'
        elif key == keyboard.Key.right:
            direction = 'right'
        
        if direction:
            self.position_display(direction)
    
    def on_key_release(self, key):
        """Handle key release to track Cmd key state"""
        if key == keyboard.Key.cmd or key == keyboard.Key.cmd_r:
            self.cmd_pressed = False
        if key in (keyboard.Key.up, keyboard.Key.down, keyboard.Key.left, keyboard.Key.right):
            self.arrows_pressed.discard(key)
    
    def check_position_collision(self, new_x, new_y, width, height):
        """Check if a position would collide with existing displays"""
        # Get all display bounds
        all_displays = self.get_displays()
        
        for display_id in all_displays:
            if display_id == self.current_external_id:
                continue  # Skip the display we're moving
            
            bounds = CGDisplayBounds(display_id)
            dx = bounds.origin.x
            dy = bounds.origin.y
            dw = bounds.size.width
            dh = bounds.size.height
            
            # Check for overlap
            if not (new_x + width <= dx or new_x >= dx + dw or 
                    new_y + height <= dy or new_y >= dy + dh):
                return True  # Collision detected
        
        return False  # No collision
    
    def position_display(self, direction):
        """Position external display in the specified direction"""
        if not self.current_external_id or not self.reference_display_id:
            print("Error: No external display or reference display found")
            return
        
        ref_bounds = CGDisplayBounds(self.reference_display_id)
        external_bounds = CGDisplayBounds(self.current_external_id)
        
        ref_x = ref_bounds.origin.x
        ref_y = ref_bounds.origin.y
        ref_width = ref_bounds.size.width
        ref_height = ref_bounds.size.height
        
        external_width = external_bounds.size.width
        external_height = external_bounds.size.height
        
        new_x = ref_x
        new_y = ref_y
        
        self.stop_blinking()
        
        if direction == 'left':
            new_x = ref_x - external_width
            new_y = ref_y
        elif direction == 'right':
            new_x = ref_x + ref_width
            new_y = ref_y
        elif direction == 'up':
            new_x = ref_x
            new_y = ref_y - external_height
        elif direction == 'down':
            new_x = ref_x
            new_y = ref_y + ref_height
        elif direction == 'top_left':
            new_x = ref_x - external_width
            new_y = ref_y - external_height
        elif direction == 'top_right':
            new_x = ref_x + ref_width
            new_y = ref_y - external_height
        elif direction == 'bottom_left':
            new_x = ref_x - external_width
            new_y = ref_y + ref_height
        elif direction == 'bottom_right':
            new_x = ref_x + ref_width
            new_y = ref_y + ref_height
        
        direction_icons = {
            'left': (self.left_icon, self.blocked_left_icon, "LEFT", "←"),
            'right': (self.right_icon, self.blocked_right_icon, "RIGHT", "→"),
            'up': (self.up_icon, self.blocked_up_icon, "ABOVE", "↑"),
            'down': (self.down_icon, self.blocked_down_icon, "BELOW", "↓"),
            'top_left': (self.top_left_icon, self.blocked_top_left_icon, "TOP-LEFT", "↖"),
            'top_right': (self.top_right_icon, self.blocked_top_right_icon, "TOP-RIGHT", "↗"),
            'bottom_left': (self.bottom_left_icon, self.blocked_bottom_left_icon, "BOTTOM-LEFT", "↙"),
            'bottom_right': (self.bottom_right_icon, self.blocked_bottom_right_icon, "BOTTOM-RIGHT", "↘"),
        }
        
        success_icon, blocked_icon, label, symbol = direction_icons[direction]
        
        if self.check_position_collision(new_x, new_y, external_width, external_height):
            self.icon = blocked_icon
            print(f"BLOCKED: Cannot position monitor {label} (collision detected) - showing red {symbol}")
            return
        
        self.icon = success_icon
        print(f"Positioning monitor {label} (icon should show {symbol})")
        
        config_ref = CGBeginDisplayConfiguration(None)[1]
        CGConfigureDisplayOrigin(config_ref, self.current_external_id, int(new_x), int(new_y))
        CGCompleteDisplayConfiguration(config_ref, kCGConfigureForSession)
        
        if self.current_external_id not in self.positioned_externals:
            self.positioned_externals.append(self.current_external_id)
        
        print("Monitor position updated successfully!")
        
        # Check if there are more monitors in the queue after positioning completes
        # Wait a moment then start the next positioning session
        if self.external_displays:
            print(f"Additional monitor(s) in queue. Starting next positioning session in 2 seconds...")
            
            # Deactivate current session first, then start next
            def transition_to_next():
                self.deactivate_positioning_mode()
                time.sleep(0.5)  # Brief pause for UI feedback
                self.start_next_positioning()
            
            threading.Timer(2.0, transition_to_next).start()
        else:
            # No more monitors to position - immediately deactivate so new plug-ins can be detected
            print("All monitors positioned. Deactivating positioning mode.")
            # Short delay to show the directional arrow, then deactivate
            threading.Timer(1.0, self.deactivate_positioning_mode).start()
    
    @rumps.clicked("Activate Positioning")
    def manual_activate(self, _):
        """Manually activate positioning mode from menu"""
        # Get all external displays
        all_externals = self.get_all_external_displays()
        
        if not all_externals:
            print("No external monitor detected. Please connect a monitor first.")
            rumps.notification("SkyScreen", "No External Monitor", "Please connect an external monitor first.")
            return
        
        # For manual activation, allow repositioning of already positioned monitors
        # Clear positioned list and add all externals to queue
        self.positioned_externals.clear()
        self.external_displays.clear()
        
        for ext in all_externals:
            if ext not in self.external_displays:
                self.external_displays.append(ext)
        
        # Set main display if not set
        if not self.main_display_id:
            self.main_display_id = self.get_main_display()
        
        # Start positioning
        if self.external_displays and not self.activation_window_active:
            print("Manual activation: 30-second positioning window started")
            self.start_next_positioning()
        elif self.activation_window_active:
            print("Positioning already active")
    
    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()


if __name__ == "__main__":
    print("Starting SkyScreen...")
    print("Look for the menu bar icon (●) in the top-right of your screen.")
    print("If you don't see it, check your system preferences for hidden menu bar items.")
    MonitorPositioner().run()
