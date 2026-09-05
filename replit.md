# SkyScreen

SkyScreen is a multi-platform menu bar/system tray application that automatically detects external monitors and lets users position them with keyboard shortcuts. Every external monitor is positioned relative to the main display, and each receives a 30-second activation window with visual feedback and collision detection.

**Platforms:**
- **macOS:** Menu bar app using Cmd + Arrow keys
- **Windows:** System tray app using Ctrl + Arrow keys

**Critical Note:** This application cannot run in Replit's Linux environment. It is designed to be downloaded and executed locally on macOS or Windows systems.

## Recent Changes (February 13, 2026)

### Diagonal Corner Positioning
- Added 4 new diagonal positioning directions: top-left (↖), top-right (↗), bottom-left (↙), bottom-right (↘)
- Press Cmd/Ctrl + two arrow keys simultaneously (e.g., Cmd + Up + Left for top-left)
- Corner arrow icons (↖↗↙↘) shown in menu bar/tray after positioning
- Red crossed diagonal arrows for collision-blocked corner positions
- Tracks multiple arrow keys pressed simultaneously for combo detection
- Updated both macOS and Windows versions

### Multi-Monitor Sequential Positioning (October 13, 2025, updated February 13, 2026)
- Added support for multiple external monitors with sequential positioning workflow
- ALL external monitors position relative to main display (up/down/left/right/corners)
- Build layouts around main screen - collision detection prevents overlapping
- Each monitor receives its own dedicated 30-second activation window
- Collision detection prevents overlapping display positions
- Visual feedback: red crossed-out arrows indicate blocked positions

### Enhanced State Management
- Queue system tracks multiple external displays awaiting positioning
- Automatic cleanup of disconnected displays from tracking lists
- Proper state reset between positioning sessions
- Fallback handling when reference displays are disconnected

### Visual Feedback Improvements
- Inactive state: Darker gray dot (●) when no positioning active
- Active state: Bright white blinking dot when positioning window open
- Success state: White directional arrows (↑↓←→↖↗↙↘) after positioning
- Blocked state: Red crossed-out arrows (→̶) when collision detected

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Framework
- **Choice:** rumps (Ridiculously Uncomplicated macOS Python Statusbar apps)
- **Rationale:** Provides simple menu bar integration for macOS without requiring complex Objective-C bridging
- **Pros:** Pythonic API, minimal boilerplate, built-in menu handling
- **Cons:** macOS-only, limited to menu bar applications

## Display Management
- **Choice:** Direct Quartz/Core Graphics API via PyObjC
- **Rationale:** Provides low-level access to display configuration, necessary for programmatic monitor positioning
- **Implementation:** Uses CGDisplayBounds, CGConfigureDisplayOrigin, and CGBeginDisplayConfiguration to detect and reposition displays
- **Alternative Considered:** Higher-level AppKit APIs, but they lack the granular control needed for display positioning

## Input Handling
- **Choice:** pynput library for keyboard event detection
- **Rationale:** Cross-platform keyboard listener with modifier key support (Cmd key detection)
- **Implementation:** Threaded keyboard listener monitors for Cmd + Arrow key combinations during activation windows
- **Pros:** Non-blocking, doesn't interfere with normal system keyboard input
- **Cons:** Requires accessibility permissions on macOS

## Visual Feedback System
- **Choice:** Dynamic icon generation using PIL (Pillow) with color-coded states
- **Rationale:** Creates custom menu bar icons programmatically to show positioning state and direction
- **Implementation:** Generates NSImage objects from PIL-drawn characters with state-based coloring:
  - Inactive: Darker gray (128, 128, 128) for idle state
  - Active: Bright white (255, 255, 255) for positioning window
  - Blocked: Red (255, 0, 0) with strikethrough line for collision-blocked positions
- **Icon States:**
  - Dot (●): Shows app state (dark gray = inactive, bright white = active/blinking)
  - Arrows (↑↓←→): Shows positioning direction (white = success, red with strikethrough = blocked)
- **Pros:** No external image assets needed, clear visual feedback for all states, collision awareness
- **Cons:** Slightly higher resource usage than static images

## Monitoring Architecture
- **Choice:** Polling-based display detection with queue management in background thread
- **Rationale:** macOS doesn't provide reliable display connection events; polling is the most stable approach
- **Implementation:** Daemon thread continuously checks CGGetActiveDisplayList for changes
  - Tracks external displays in a sequential queue
  - Detects both connections (new displays) and disconnections (cleanup)
  - Automatically prunes disconnected displays from all tracking lists
- **Layout Positioning:** All external monitors position relative to main display, building layouts around the main screen
- **Activation Window:** 30-second timer-based window for each monitor, with proper reset between sessions
- **Collision Detection:** Checks display bounds overlap before positioning; shows red crossed arrows when blocked
- **Pros:** Reliable detection, handles multiple monitors intelligently, prevents display overlap
- **Cons:** Constant background polling (mitigated by sleep intervals)

## Threading Model
- **Monitor Thread:** Daemon thread for continuous display detection
- **Timer Thread:** Handles 30-second activation window countdown
- **Keyboard Listener:** Separate thread for non-blocking input detection
- **Main Thread:** Runs rumps event loop and handles UI updates

# External Dependencies

## macOS Version
- **pyobjc-framework-Quartz:** Low-level display management (CGDisplay APIs)
- **pyobjc-framework-Cocoa:** AppKit integration for NSImage creation
- **rumps (≥0.4.0):** Menu bar application framework
- **pynput (≥1.7.6):** Keyboard event monitoring for shortcut detection
- **Pillow (≥10.0.0):** Dynamic icon image generation

## Windows Version
- **ctypes (builtin):** Windows API access for display management
- **pystray (≥0.19.4):** System tray icon framework
- **pynput (≥1.7.6):** Keyboard event monitoring for shortcut detection
- **Pillow (≥10.0.0):** Dynamic icon image generation
- **PyInstaller (≥6.0.0):** For creating standalone executable

## System Requirements
- **macOS:** Accessibility permissions required for keyboard monitoring
- **Windows:** May require running as Administrator for display changes
- **Python:** Python 3.x

## Installation Mechanism

### Recommended: .app Bundle (py2app)
- **setup.py:** py2app configuration for building macOS application bundle
- **build_app.sh:** Automated build script that creates "SkyScreen.app"
- **Distribution:** Double-clickable .app that can be added to Login Items for auto-start
- **LSUIElement:** Configured to hide from Dock, showing only in menu bar

### Alternative: Background Service (Launch Agent)
- **install_background.sh:** Launch Agent installer for running the app in background without terminal window
- **com.skyscreen.app.plist:** macOS Launch Agent configuration for automatic background execution
- **Auto-restart:** KeepAlive ensures the app restarts if it crashes
- **Logging:** Output logs to /tmp/skyscreen.log and /tmp/skyscreen_error.log

### Dependencies
- **setup_macos.sh:** Bash script for automated dependency installation on macOS
- **requirements.txt:** Standard pip requirements file including py2app for building