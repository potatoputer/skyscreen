@echo off
echo ============================================
echo Building SkyScreen for Windows
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements_win.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Building executable...
pyinstaller --onefile --windowed --icon=monitor_icon.ico --name="SkyScreen" monitor_position_win.py
if errorlevel 1 (
    echo ERROR: Failed to build executable
    pause
    exit /b 1
)

echo.
echo ============================================
echo Build complete!
echo ============================================
echo.
echo Executable created at: dist\SkyScreen.exe
echo.
echo Next steps:
echo 1. Run "SkyScreen.exe" to test
echo 2. Run create_installer.bat to create the installer
echo.
pause
