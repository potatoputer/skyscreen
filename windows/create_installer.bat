@echo off
echo ============================================
echo Creating SkyScreen Installer
echo ============================================
echo.

REM Check if Inno Setup is installed
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else (
    echo ERROR: Inno Setup 6 is not installed
    echo Please download and install from: https://jrsoftware.org/isdl.php
    echo.
    pause
    exit /b 1
)

REM Check if the executable exists
if not exist "dist\SkyScreen.exe" (
    echo ERROR: Executable not found!
    echo Please run build_exe.bat first
    pause
    exit /b 1
)

echo Creating installer...
%ISCC% installer_script.iss
if errorlevel 1 (
    echo ERROR: Failed to create installer
    pause
    exit /b 1
)

echo.
echo ============================================
echo Installer created successfully!
echo ============================================
echo.
echo Installer location: installer_output\SkyScreen_Setup.exe
echo.
pause
