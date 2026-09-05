#!/bin/bash

# Build SkyScreen.app using py2app alias mode
# This creates a lightweight app wrapper without bundling all Python libraries

set -e

echo "🔨 Building SkyScreen.app (alias mode)..."
echo ""

# Check if py2app is installed
if ! python3 -c "import py2app" 2>/dev/null; then
    echo "📦 Installing py2app..."
    pip3 install py2app
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Build the app in alias mode (lightweight wrapper)
echo "🚀 Building application bundle..."
python3 setup.py py2app --alias

echo ""
echo "✅ Build complete!"
echo ""
echo "📁 Application created at: dist/SkyScreen.app"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Move the app to your Applications folder:"
echo "   mv 'dist/SkyScreen.app' /Applications/"
echo ""
echo "2. IMPORTANT: Keep the original folder!"
echo "   The .app is linked to this folder, so don't delete it."
echo ""
echo "3. Double-click 'SkyScreen.app' to run it"
echo "   (Look for the ● icon in your menu bar)"
echo ""
echo "4. OPTIONAL - To run on login:"
echo "   a. Go to System Settings → General → Login Items"
echo "   b. Click the '+' button under 'Open at Login'"
echo "   c. Select 'SkyScreen' from Applications"
echo ""
echo "5. Grant Accessibility permissions when prompted:"
echo "   System Settings → Privacy & Security → Accessibility"
echo "   Enable 'SkyScreen'"
echo ""
