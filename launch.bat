@echo off
setlocal enabledelayedexpansion
title Arduino Flight Controller

set "SCRIPT_DIR=%~dp0"
set "APP_DIR=%SCRIPT_DIR%app"
set "REQUIREMENTS=%APP_DIR%\requirements.txt"

echo.
echo  ============================================
echo    Arduino Flight Controller
echo  ============================================
echo.

rem ── 1. Python ─────────────────────────────────────────────────────────────
echo  [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo         Python is not installed or not in PATH.
    echo.
    echo         To fix this:
    echo           1. Go to https://www.python.org/downloads/
    echo           2. Download Python 3.10 or newer
    echo           3. Run the installer
    echo           4. On the first screen, check "Add Python to PATH"
    echo           5. Complete the install, then run this file again
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo         %%v

rem ── 2. pip packages ───────────────────────────────────────────────────────
echo.
echo  [2/4] Installing Python packages...
python -m pip install -r "%REQUIREMENTS%" --quiet
if %errorlevel% neq 0 (
    echo.
    echo         ERROR: Package installation failed.
    echo         Try running this manually:
    echo           pip install -r app\requirements.txt
    echo.
    pause
    exit /b 1
)
echo         pyserial, pyvjoy ready.

rem ── 3. vJoy driver ────────────────────────────────────────────────────────
echo.
echo  [3/4] Checking vJoy driver...
if exist "C:\Program Files\vJoy\x64\vJoyInterface.dll" (
    echo         vJoy found.
) else (
    echo.
    echo         WARNING: vJoy driver not detected.
    echo         The app needs vJoy to send joystick data to your flight sim.
    echo.
    echo         Install from: https://sourceforge.net/projects/vjoystick/
    echo         After installing, open "Configure vJoy" and enable Device 1
    echo         with axes X, Y, Z and at least 1 button, then click Apply.
    echo.
    choice /c YN /m "         Launch anyway (Y) or exit to install vJoy first (N)?"
    if errorlevel 2 (
        echo.
        echo         Exiting. Run launch.bat again after installing vJoy.
        pause
        exit /b 0
    )
)

rem ── 4. Launch app ─────────────────────────────────────────────────────────
echo.
echo  [4/4] Starting flight controller app...
echo.
cd /d "%APP_DIR%"
python main.py
set "APP_EXIT=%errorlevel%"

echo.
if %APP_EXIT% neq 0 (
    echo  App closed with an error. See the message above.
    pause
) else (
    echo  App closed. Run launch.bat to start again.
    timeout /t 3 >nul
)
