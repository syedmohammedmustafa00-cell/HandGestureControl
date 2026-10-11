@echo off
echo ======================================================
echo    Starting Hand Gesture Control (Python + OpenCV)
echo ======================================================
cd /d "%~dp0"

if not exist "%~dp0venv\Scripts\python.exe" (
    echo [INFO] Setting up virtual environment for the first time...
    python -m venv venv
    echo [INFO] Installing required packages...
    "%~dp0venv\Scripts\pip.exe" install -r "%~dp0requirements.txt"
)

"%~dp0venv\Scripts\python.exe" "%~dp0main.py"
pause
