#!/bin/bash
cd "$(dirname "$0")"

echo "Cleaning old builds..."
rm -rf build dist *.spec dist/dmg "EBU R 128 Scanner.dmg"

echo "Building Mac application with PyInstaller..."
./venv/bin/pyinstaller --noconfirm --windowed --icon="logo_tim/EBUR128_scanner_icon-macOS-Default-1024x1024@1x.png" --name "EBU R 128 Scanner" main.py

echo "Preparing DMG folder..."
mkdir -p dist/dmg
cp -r "dist/EBU R 128 Scanner.app" dist/dmg/
ln -s /Applications dist/dmg/Applications

echo "Creating DMG..."
hdiutil create -volname "EBU R 128 Scanner" -srcfolder dist/dmg -ov -format UDZO "EBU R 128 Scanner.dmg"

echo "Done! EBU R 128 Scanner.dmg is ready."
