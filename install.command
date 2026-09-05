#!/bin/bash
# Double-click installer for SkyScreen 1.1.0

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "Installing SkyScreen 1.1.0"
echo "============================================"
echo ""

if [ "$(uname -s)" != "Darwin" ]; then
    echo "Error: This installer must be run on macOS."
    read -r -p "Press Return to close..."
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is required."
    echo "Install Python 3 from https://www.python.org/downloads/macos/"
    read -r -p "Press Return to close..."
    exit 1
fi

./setup_macos.sh
./build_app.sh

INSTALL_DIR="$HOME/Applications"
APP_PATH="$INSTALL_DIR/SkyScreen.app"

mkdir -p "$INSTALL_DIR"
if [ -d "$APP_PATH" ]; then
    echo "Replacing the previous SkyScreen installation..."
    rm -rf "$APP_PATH"
fi

cp -R "dist/SkyScreen.app" "$APP_PATH"

echo ""
echo "Installation complete:"
echo "  $APP_PATH"
echo ""
echo "Opening SkyScreen..."
open "$APP_PATH"
echo ""
echo "If macOS blocks keyboard shortcuts, enable SkyScreen in:"
echo "System Settings > Privacy & Security > Accessibility"
echo ""
read -r -p "Press Return to close..."