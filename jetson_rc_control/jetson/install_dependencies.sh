#!/bin/bash
# Installation script for Jetson RC Control dependencies
# Run this on Linux/Jetson

echo "========================================"
echo "Installing RC Control Dependencies"
echo "========================================"
echo

echo "Uninstalling conflicting 'serial' package..."
pip3 uninstall serial -y

echo
echo "Installing required packages..."
pip3 install -r requirements.txt

echo
echo "Adding user to dialout group for serial permissions..."
sudo usermod -aG dialout $USER

echo
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo
echo "IMPORTANT: Log out and back in for serial permissions to take effect"
echo "Then you can run: python3 teleop_rc.py"
echo
