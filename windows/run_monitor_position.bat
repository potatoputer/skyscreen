@echo off
echo Starting SkyScreen...
echo Look for the icon in the system tray (bottom-right corner)
echo Use Ctrl + Arrow keys to position monitors
echo.
pythonw monitor_position_win.py
if errorlevel 1 (
    echo Falling back to python...
    python monitor_position_win.py
)
