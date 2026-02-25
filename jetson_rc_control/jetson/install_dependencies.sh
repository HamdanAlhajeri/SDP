#!/bin/bash
# Installation script for Jetson RC Control dependencies
# Run this on Linux/Jetson

echo "========================================"
echo "Installing RC Control Dependencies"
echo "========================================"
echo

echo "Installing required packages with sudo..."
sudo pip3 install -r requirements.txt

echo
echo "Verifying installation..."
python3 -c "import pygame, Jetson.GPIO; print('✓ Dependencies installed successfully!')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠ Warning: Could not verify installation. You may need to install manually."
fi

echo
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo
echo "IMPORTANT: Run the script with sudo for GPIO access:"
echo "  sudo python3 teleop_rc.py"
echo
