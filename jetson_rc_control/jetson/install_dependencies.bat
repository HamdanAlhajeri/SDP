@echo off
REM Installation script for Jetson RC Control dependencies
REM Note: This is for development/testing only
REM Jetson.GPIO will not work on Windows - this is for syntax checking

echo ========================================
echo Installing RC Control Dependencies
echo ========================================
echo.

echo NOTE: Jetson.GPIO will not function on Windows!
echo This script is for installing pygame for development/testing only.
echo.

echo Installing required packages from requirements.txt...
pip install -r requirements.txt

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo WARNING: This script requires Jetson hardware to run with GPIO.
echo For actual testing, deploy to Jetson and run with sudo.
echo.
pause
