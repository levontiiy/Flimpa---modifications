@echo off
REM ============================================================
REM  FLIMPA online installer - Windows
REM  Installs all required libraries directly from the internet
REM  (PyPI) into your current Python. No virtual environment.
REM ============================================================
cd /d "%~dp0"

echo Using Python:
python --version
if errorlevel 1 (
  echo.
  echo ERROR: Python was not found. Install Python 3.13 from python.org
  echo and tick "Add python.exe to PATH" during setup, then run this again.
  echo.
  pause
  exit /b 1
)

echo.
echo Upgrading pip ...
python -m pip install --upgrade pip

echo.
echo Installing FLIMPA libraries from the internet ...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo ERROR: Installation failed. Check your internet connection and try again.
  echo.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo  Done. To start FLIMPA, run:
echo     python main.py
echo ============================================================
pause
