#!/usr/bin/env python3
"""
SkyScreen for Windows
Detects external monitor connections and allows positioning with Ctrl + Arrow keys
"""

import threading
import time
import tempfile
import os
import sys
from pynput import keyboard
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item
import ctypes
from ctypes import wintypes

# Windows API constants
ENUM_CURRENT_SETTINGS = -1
ENUM_REGISTRY_SETTINGS = -2
CDS_UPDATEREGISTRY = 0x00000001
CDS_TEST = 0x00000002
CDS_FULLSCREEN = 0x00000004
CDS_GLOBAL = 0x00000008
CDS_SET_PRIMARY = 0x00000010
CDS_RESET = 0x40000000
CDS_NORESET = 0x10000000
DISP_CHANGE_SUCCESSFUL = 0
DISP_CHANGE_RESTART = 1
DM_POSITION = 0x00000020
DM_PELSWIDTH = 0x00080000
DM_PELSHEIGHT = 0x00100000

# Load Windows DLLs
user32 = ctypes.windll.user32
shcore = None
try:
    shcore = ctypes.windll.shcore
except:
    pass


class DEVMODE(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("dmPositionX", wintypes.LONG),
        ("dmPositionY", wintypes.LONG),
        ("dmDisplayOrientation", wintypes.DWORD),
        ("dmDisplayFixedOutput", wintypes.DWORD),
        ("dmColor", wintypes.SHORT),
        ("dmDuplex", wintypes.SHORT),
        ("dmYResolution", wintypes.SHORT),
        ("dmTTOption", wintypes.SHORT),
        ("dmCollate", wintypes.SHORT),
        ("dmFormName", ctypes.c_wchar * 32),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
        ("dmICMMethod", wintypes.DWORD),
        ("dmICMIntent", wintypes.DWORD),
        ("dmMediaType", wintypes.DWORD),
        ("dmDitherType", wintypes.DWORD),
        ("dmReserved1", wintypes.DWORD),
        ("dmReserved2", wintypes.DWORD),
        ("dmPanningWidth", wintypes.DWORD),
        ("dmPanningHeight", wintypes.DWORD),
    ]


class DISPLAY_DEVICE(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128),
    ]


class MonitorPositioner:
    def __init__(self):
        self.activation_window_active = False
        self.activation_timer = None
        self.keyboard_listener = None
        self.ctrl_pressed = False
        self.arrows_pressed = set()
        self.blink_timer = None
        self.blink_state = False
        
        self.current_displays = set()
        self.external_displays = []
        self.positioned_externals = []
        self.current_external_name = None
        self.reference_display_name = None
        self.primary_display_name = None
        
        self.icon = None
        self.running = True
        
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
        
        self.current_icon = self.default_icon
    
    def create_icon_image(self, symbol, inactive=False, blocked=False):
        """Create a system tray icon with the given symbol"""
        img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        draw.ellipse([2, 2, 62, 62], fill=(40, 40, 40, 255))
        
        if blocked:
            color = (255, 80, 80, 255)
        elif inactive:
            color = (128, 128, 128, 255)
        else:
            color = (255, 255, 255, 255)
        
        try:
            font = ImageFont.truetype("seguisym.ttf", 36)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
        
        if symbol:
            bbox = draw.textbbox((0, 0), symbol, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (64 - text_width) // 2
            y = (64 - text_height) // 2 - 4
            draw.text((x, y), symbol, fill=color, font=font)
        
        if blocked and symbol in ["↖", "↗", "↙", "↘"]:
            draw.line([(12, 12), (52, 52)], fill=(255, 80, 80, 255), width=4)
        
        if blocked and symbol in ["↑", "↓", "←", "→"]:
            draw.line([(12, 32), (52, 32)], fill=(255, 80, 80, 255), width=4)
        
        return img
    
    def get_displays(self):
        """Get all active displays"""
        displays = {}
        i = 0
        while True:
            display_device = DISPLAY_DEVICE()
            display_device.cb = ctypes.sizeof(display_device)
            
            if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(display_device), 0):
                break
            
            if display_device.StateFlags & 0x00000001:
                devmode = DEVMODE()
                devmode.dmSize = ctypes.sizeof(devmode)
                
                if user32.EnumDisplaySettingsW(display_device.DeviceName, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode)):
                    displays[display_device.DeviceName] = {
                        'name': display_device.DeviceName,
                        'string': display_device.DeviceString,
                        'x': devmode.dmPositionX,
                        'y': devmode.dmPositionY,
                        'width': devmode.dmPelsWidth,
                        'height': devmode.dmPelsHeight,
                        'is_primary': bool(display_device.StateFlags & 0x00000004)
                    }
            i += 1
        
        return displays
    
    def get_primary_display(self):
        """Find the primary display"""
        displays = self.get_displays()
        for name, info in displays.items():
            if info['is_primary']:
                return name
        return list(displays.keys())[0] if displays else None
    
    def get_external_displays(self):
        """Get all non-primary displays"""
        displays = self.get_displays()
        externals = []
        for name, info in displays.items():
            if not info['is_primary']:
                externals.append(name)
        return externals
    
    def monitor_displays(self):
        """Monitor for new display connections"""
        while self.running:
            try:
                current = set(self.get_displays().keys())
                
                if len(current) < len(self.current_displays):
                    disconnected = self.current_displays - current
                    self.positioned_externals = [d for d in self.positioned_externals if d not in disconnected]
                    self.external_displays = [d for d in self.external_displays if d not in disconnected]
                    
                    if self.current_external_name in disconnected:
                        self.current_external_name = None
                        self.deactivate_positioning_mode()
                    
                    print(f"Detected {len(disconnected)} display(s) disconnected. Cleaned up tracking.")
                
                if current != self.current_displays and len(current) > len(self.current_displays):
                    all_externals = self.get_external_displays()
                    
                    new_externals = [
                        d for d in all_externals 
                        if d not in self.positioned_externals 
                        and d not in self.external_displays
                        and d != self.current_external_name
                    ]
                    
                    if new_externals:
                        self.external_displays.extend(new_externals)
                        print(f"Detected {len(new_externals)} new external display(s). Added to positioning queue.")
                        
                        if not self.primary_display_name:
                            self.primary_display_name = self.get_primary_display()
                        
                        if not self.activation_window_active and self.external_displays:
                            self.start_next_positioning()
                
                self.current_displays = current
            except Exception as e:
                print(f"Error in monitor_displays: {e}")
            
            time.sleep(2)
    
    def start_next_positioning(self):
        """Start positioning the next external monitor in the queue"""
        if not self.external_displays:
            print("No more monitors to position")
            self.current_external_name = None
            self.reference_display_name = None
            return
        
        if self.activation_window_active:
            self.deactivate_positioning_mode()
        
        self.current_external_name = self.external_displays.pop(0)
        
        self.reference_display_name = self.primary_display_name
        monitor_num = len(self.positioned_externals) + 1
        print(f"Positioning external monitor #{monitor_num} (relative to primary display)")
        
        self.activate_positioning_mode()
    
    def activate_positioning_mode(self):
        """Activate 30-second window for positioning"""
        if self.activation_window_active:
            return
        
        self.activation_window_active = True
        self.ctrl_pressed = False
        self.arrows_pressed = set()
        
        self.start_blinking()
        
        try:
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.keyboard_listener.start()
        except Exception as e:
            print(f"Keyboard listener failed: {e}")
        
        self.activation_timer = threading.Timer(30.0, self.deactivate_positioning_mode)
        self.activation_timer.start()
        
        print("Positioning mode activated! Press Ctrl + Arrow keys to position monitor.")
    
    def start_blinking(self):
        """Start blinking the icon"""
        self.blink_state = True
        self.blink()
    
    def blink(self):
        """Toggle icon visibility for blinking effect"""
        if not self.activation_window_active:
            return
        
        if self.blink_state:
            self.update_icon(self.blank_icon)
        else:
            self.update_icon(self.active_icon)
        
        self.blink_state = not self.blink_state
        
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
        
        self.stop_blinking()
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        
        if self.activation_timer:
            self.activation_timer.cancel()
            self.activation_timer = None
        
        self.update_icon(self.default_icon)
        
        if not self.external_displays:
            self.current_external_name = None
            self.reference_display_name = None
        
        print("Positioning window closed.")
    
    def on_key_press(self, key):
        """Handle keyboard input during activation window"""
        if not self.activation_window_active:
            return
        
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = True
            return
        
        if key in (keyboard.Key.up, keyboard.Key.down, keyboard.Key.left, keyboard.Key.right):
            self.arrows_pressed.add(key)
        
        if not self.ctrl_pressed:
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
        """Handle key release to track Ctrl key state"""
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False
        if key in (keyboard.Key.up, keyboard.Key.down, keyboard.Key.left, keyboard.Key.right):
            self.arrows_pressed.discard(key)
    
    def check_position_collision(self, new_x, new_y, width, height):
        """Check if a position would collide with existing displays"""
        displays = self.get_displays()
        
        for name, info in displays.items():
            if name == self.current_external_name:
                continue
            
            dx = info['x']
            dy = info['y']
            dw = info['width']
            dh = info['height']
            
            if not (new_x + width <= dx or new_x >= dx + dw or 
                    new_y + height <= dy or new_y >= dy + dh):
                return True
        
        return False
    
    def position_display(self, direction):
        """Position external display in the specified direction"""
        if not self.current_external_name or not self.reference_display_name:
            print("Error: No external display or reference display found")
            return
        
        displays = self.get_displays()
        
        if self.current_external_name not in displays or self.reference_display_name not in displays:
            print("Error: Display not found")
            return
        
        ref = displays[self.reference_display_name]
        ext = displays[self.current_external_name]
        
        ref_x = ref['x']
        ref_y = ref['y']
        ref_width = ref['width']
        ref_height = ref['height']
        
        ext_width = ext['width']
        ext_height = ext['height']
        
        self.stop_blinking()
        
        new_x = ref_x
        new_y = ref_y
        
        if direction == 'left':
            new_x = ref_x - ext_width
            new_y = ref_y
        elif direction == 'right':
            new_x = ref_x + ref_width
            new_y = ref_y
        elif direction == 'up':
            new_x = ref_x
            new_y = ref_y - ext_height
        elif direction == 'down':
            new_x = ref_x
            new_y = ref_y + ref_height
        elif direction == 'top_left':
            new_x = ref_x - ext_width
            new_y = ref_y - ext_height
        elif direction == 'top_right':
            new_x = ref_x + ref_width
            new_y = ref_y - ext_height
        elif direction == 'bottom_left':
            new_x = ref_x - ext_width
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
        
        if self.check_position_collision(new_x, new_y, ext_width, ext_height):
            self.update_icon(blocked_icon)
            print(f"BLOCKED: Cannot position monitor {label} (collision detected)")
            return
        
        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(devmode)
        
        if user32.EnumDisplaySettingsW(self.current_external_name, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode)):
            devmode.dmPositionX = new_x
            devmode.dmPositionY = new_y
            devmode.dmFields = DM_POSITION
            
            result = user32.ChangeDisplaySettingsExW(
                self.current_external_name,
                ctypes.byref(devmode),
                None,
                CDS_UPDATEREGISTRY | CDS_NORESET,
                None
            )
            
            user32.ChangeDisplaySettingsExW(None, None, None, 0, None)
            
            if result == DISP_CHANGE_SUCCESSFUL:
                self.update_icon(success_icon)
                print(f"Positioned monitor {label} ({symbol})")
                
                if self.current_external_name not in self.positioned_externals:
                    self.positioned_externals.append(self.current_external_name)
                
                print("Monitor position updated successfully!")
                
                if self.external_displays:
                    print(f"Additional monitor(s) in queue. Starting next positioning session in 2 seconds...")
                    
                    def transition_to_next():
                        self.deactivate_positioning_mode()
                        time.sleep(0.5)
                        self.start_next_positioning()
                    
                    threading.Timer(2.0, transition_to_next).start()
                else:
                    print("All monitors positioned. Deactivating positioning mode.")
                    threading.Timer(1.0, self.deactivate_positioning_mode).start()
            else:
                print(f"Failed to change display settings. Error code: {result}")
    
    def update_icon(self, new_icon):
        """Update the system tray icon"""
        self.current_icon = new_icon
        if self.icon:
            self.icon.icon = new_icon
    
    def manual_activate(self, icon, item):
        """Manually activate positioning mode from menu"""
        all_externals = self.get_external_displays()
        
        if not all_externals:
            print("No external monitor detected. Please connect a monitor first.")
            return
        
        # For manual activation, allow repositioning of already positioned monitors
        # Clear positioned list and add all externals to queue
        self.positioned_externals.clear()
        self.external_displays.clear()
        
        for ext in all_externals:
            if ext not in self.external_displays:
                self.external_displays.append(ext)
        
        if not self.primary_display_name:
            self.primary_display_name = self.get_primary_display()
        
        if self.external_displays and not self.activation_window_active:
            print("Manual activation: 30-second positioning window started")
            self.start_next_positioning()
        elif self.activation_window_active:
            print("Positioning already active")
    
    def quit_app(self, icon, item):
        """Quit the application"""
        self.running = False
        self.deactivate_positioning_mode()
        icon.stop()
    
    def run(self):
        """Run the application"""
        print("Starting SkyScreen for Windows...")
        print("Look for the icon in the system tray.")
        print("Use Ctrl + Arrow keys to position monitors.")
        
        monitor_thread = threading.Thread(target=self.monitor_displays, daemon=True)
        monitor_thread.start()
        
        menu = pystray.Menu(
            item('Activate Positioning', self.manual_activate),
            item('Quit', self.quit_app)
        )
        
        self.icon = pystray.Icon(
            "SkyScreen",
            self.current_icon,
            "SkyScreen",
            menu
        )
        
        self.icon.run()


if __name__ == "__main__":
    app = MonitorPositioner()
    app.run()
