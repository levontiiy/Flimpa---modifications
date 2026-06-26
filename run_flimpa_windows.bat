@echo off
REM Start FLIMPA using the local offline-installed virtual environment.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo FLIMPA is not installed yet. Run this first:
  echo     offline\install_offline_windows.bat
  echo.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
