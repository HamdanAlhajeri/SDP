@echo off
REM Installation script for Jetson RC Control dependencies
REM Run this on Windows before testing the script

echo ========================================
echo Installing RC Control Dependencies
echo ========================================
echo.

echo Uninstalling conflicting 'serial' package...
pip uninstall serial -y

echo.
echo Installing required packages from requirements.txt...
pip install -r requirements.txt

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now run: python teleop_rc.py
echo.
pause
