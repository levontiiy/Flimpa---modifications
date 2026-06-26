@echo off
REM ============================================================
REM  FLIMPA offline installer - Windows 64-bit / Python 3.13
REM  Installs all dependencies from the bundled wheels in
REM  offline\wheels-windows-py313 with no internet access.
REM ============================================================
setlocal
cd /d "%~dp0\.."

set "PYCMD="
py -3.13 -c "import sys" >nul 2>&1 && set "PYCMD=py -3.13"
if not defined PYCMD (
  python -c "import sys; assert sys.version_info[:2]==(3,13)" >nul 2>&1 && set "PYCMD=python"
)
if not defined PYCMD (
  echo.
  echo ERROR: Python 3.13 ^(64-bit^) was not found on this machine.
  echo The bundled wheels are built specifically for Python 3.13.
  echo Install Python 3.13 from python.org ^(or use the offline installer
  echo you placed in this folder^), then run this script again.
  echo.
  pause
  exit /b 1
)

echo Using Python:
%PYCMD% --version

REM Remove any stale .venv (e.g. a leftover symlink/file copied from another
REM computer or OS). Python's venv refuses to run if .venv already exists as a
REM file or symlink, giving "Unable to create directory".
if exist ".venv\" (
  echo Removing existing .venv folder ...
  rmdir /s /q ".venv"
)
if exist ".venv" (
  echo Removing stale .venv item ...
  del /f /q ".venv"
)

echo.
echo Creating virtual environment (.venv) ...
%PYCMD% -m venv .venv
if errorlevel 1 (
  echo ERROR: Could not create the virtual environment.
  pause
  exit /b 1
)

echo.
echo Installing FLIMPA dependencies from bundled wheels (offline) ...
".venv\Scripts\python.exe" -m pip install --no-index --find-links "offline\wheels-windows-py313" -r requirements.txt
if errorlevel 1 (
  echo ERROR: Offline install failed.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo  Done. To start FLIMPA, run:
echo     .venv\Scripts\python.exe main.py
echo ============================================================
pause
