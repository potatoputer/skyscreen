#!/bin/bash
# Setup script for SkyScreen on macOS

set -e

echo "Setting up SkyScreen for macOS..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    echo "Visit: https://www.python.org/downloads/"
    exit 1
fi

# Install dependencies
echo "Installing Python dependencies..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
python3 -m pip install -r requirements.txt

# Finder may strip or lose executable permissions after downloading/unzipping.
chmod +x run_monitor_position.command

echo ""
echo "Setup complete!"
echo ""
echo "To run SkyScreen:"
echo "  python3 monitor_position.py"
echo ""
echo "The app will appear in your menu bar."
echo "When you connect an external monitor, you'll have 30 seconds to:"
echo "  - Press Cmd + Left Arrow to position monitor on the left"
echo "  - Press Cmd + Right Arrow to position monitor on the right"
echo "  - Press Cmd + Up Arrow to position monitor above"
echo "  - Press Cmd + Down Arrow to position monitor below"
echo ""
