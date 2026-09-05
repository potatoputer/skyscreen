#!/bin/bash

# SkyScreen - Background Installation Script
# This script sets up the app to run in the background automatically

set -e

echo "🔧 Setting up SkyScreen to run in background..."

# Get the current directory (where the script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_FILE="com.skyscreen.app.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

# Detect the Python interpreter with dependencies installed
# Try to find pythonw first (GUI mode), fallback to python3
if command -v pythonw &> /dev/null; then
    PYTHON_PATH=$(which pythonw)
elif command -v python3 &> /dev/null; then
    PYTHON_PATH=$(which python3)
else
    echo "❌ Error: Python 3 not found"
    exit 1
fi

echo "📍 Using Python: $PYTHON_PATH"

# Ensure LaunchAgents directory exists
mkdir -p "$LAUNCH_AGENTS_DIR"

# Update the plist with the actual script path and Python interpreter
echo "📝 Configuring launch agent..."
sed -e "s|SCRIPT_PATH_PLACEHOLDER|$SCRIPT_DIR|g" \
    -e "s|/usr/bin/python3|$PYTHON_PATH|g" \
    "$SCRIPT_DIR/$PLIST_FILE" > "$LAUNCH_AGENTS_DIR/$PLIST_FILE"

# Unload if already loaded (in case of reinstall)
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_FILE" 2>/dev/null || true

# Load the launch agent
echo "🚀 Loading launch agent..."
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_FILE"

echo ""
echo "✅ Success! SkyScreen is now running in the background."
echo ""
echo "📋 Status:"
echo "   • App will auto-start on login"
echo "   • No terminal window required"
echo "   • Runs silently in menu bar"
echo ""
echo "📁 Logs location:"
echo "   • Output: /tmp/skyscreen.log"
echo "   • Errors: /tmp/skyscreen_error.log"
echo ""
echo "🛑 To stop the background service:"
echo "   launchctl unload ~/Library/LaunchAgents/$PLIST_FILE"
echo ""
echo "🔄 To restart the service:"
echo "   launchctl unload ~/Library/LaunchAgents/$PLIST_FILE"
echo "   launchctl load ~/Library/LaunchAgents/$PLIST_FILE"
echo ""
