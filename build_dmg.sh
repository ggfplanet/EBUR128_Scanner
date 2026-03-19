#!/bin/bash
cd "$(dirname "$0")"

echo "Cleaning old builds..."
rm -rf build dist *.spec dist/dmg EBUR128_Scanner.dmg

echo "Building Mac application with PyInstaller..."
./venv/bin/pyinstaller --noconfirm --windowed --icon="logo_tim/EBUR128_scanner_icon-macOS-Default-1024x1024@1x.png" --name "EBUR128_Scanner" main.py

echo "Preparing DMG folder..."
mkdir -p dist/dmg
cp -r dist/EBUR128_Scanner.app dist/dmg/
ln -s /Applications dist/dmg/Applications

echo "Creating DMG..."
hdiutil create -volname "EBUR128_Scanner" -srcfolder dist/dmg -ov -format UDZO EBUR128_Scanner.dmg

echo "Done! EBUR128_Scanner.dmg is ready."
