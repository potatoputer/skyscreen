@echo off
echo ============================================
echo SkyScreen - Quick Setup
echo ============================================
echo.
echo This script will install the application for you.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
pip install pynput Pillow pystray
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ============================================
echo Setup complete!
echo ============================================
echo.
echo To run the application:
echo   python monitor_position_win.py
echo.
echo Or double-click 'run_monitor_position.bat'
echo.
pause
