#!/bin/bash
# Build a native macOS .pkg installer for SkyScreen 1.1.0

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="SkyScreen"
VERSION="1.1.0"
IDENTIFIER="com.skyscreen.app"
PKG_PATH="$SCRIPT_DIR/dist/$APP_NAME-$VERSION.pkg"

echo "============================================"
echo "Creating $APP_NAME $VERSION macOS installer"
echo "============================================"
echo ""

if [ "$(uname -s)" != "Darwin" ]; then
    echo "Error: The native macOS installer must be built on a Mac."
    read -r -p "Press Return to close..."
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is required."
    echo "Install it from https://www.python.org/downloads/macos/"
    read -r -p "Press Return to close..."
    exit 1
fi

if ! command -v pkgbuild >/dev/null 2>&1; then
    echo "Error: Apple's pkgbuild tool is missing."
    echo "Install the Xcode Command Line Tools with: xcode-select --install"
    read -r -p "Press Return to close..."
    exit 1
fi

chmod +x setup_macos.sh build_app.sh
./setup_macos.sh
./build_app.sh

APP_PATH="$SCRIPT_DIR/dist/$APP_NAME.app"
if [ ! -d "$APP_PATH" ]; then
    echo "Error: The app build did not create $APP_PATH"
    read -r -p "Press Return to close..."
    exit 1
fi

rm -f "$PKG_PATH"
pkgbuild \
    --component "$APP_PATH" \
    --install-location "/Applications" \
    --identifier "$IDENTIFIER" \
    --version "$VERSION" \
    "$PKG_PATH"

echo ""
echo "Installer created successfully:"
echo "  $PKG_PATH"
echo ""
echo "Double-click the .pkg file to install SkyScreen."
open -R "$PKG_PATH"
read -r -p "Press Return to close..."