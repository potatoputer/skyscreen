#!/bin/bash
# Simple launcher for SkyScreen
# Double-click this file to run the app

cd "$(dirname "$0")"

PYTHON_BIN="$(command -v python3)"

if [ -z "$PYTHON_BIN" ]; then
    echo "Error: Python 3 is not installed."
    echo "Install Python 3, then run setup_macos.sh again."
    read -r -p "Press Return to close..."
    exit 1
fi

"$PYTHON_BIN" monitor_position.py
status=$?

if [ "$status" -ne 0 ]; then
    echo ""
    echo "SkyScreen could not start."
    echo "Run ./setup_macos.sh, then try again."
    read -r -p "Press Return to close..."
fi

exit "$status"
