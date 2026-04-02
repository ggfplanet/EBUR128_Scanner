#!/bin/bash
cd "$(dirname "$0")"

echo "Cleaning old builds..."
rm -rf build dist "EBU R 128 Scanner.dmg"

echo "Building Mac application with PyInstaller (Apple Silicon only)..."
# Wir setzen --target-arch arm64 um Intel-Unterstützung zu entfernen und Dateigröße zu sparen.
# Zudem schließen wir nicht benötigte PySide6 und Matplotlib Module aus.
./venv/bin/pyinstaller --noconfirm --windowed \
    --target-arch arm64 \
    --icon="logo_tim/EBUR128_scanner_icon-macOS-Default-1024x1024@1x.png" \
    --name "EBU R 128 Scanner" \
    --exclude-module PySide6.QtWebEngineCore \
    --exclude-module PySide6.QtWebEngineWidgets \
    --exclude-module PySide6.QtQml \
    --exclude-module PySide6.QtQuick \
    --exclude-module PySide6.QtSql \
    --exclude-module PySide6.QtXml \
    --exclude-module PySide6.QtTest \
    --exclude-module PySide6.QtDBus \
    --exclude-module PySide6.QtBluetooth \
    --exclude-module PySide6.QtNfc \
    --exclude-module PySide6.QtMultimedia \
    --exclude-module PySide6.QtPositioning \
    --exclude-module PySide6.QtLocation \
    --exclude-module PySide6.QtSensors \
    --exclude-module PySide6.QtSerialPort \
    --exclude-module matplotlib.backends.backend_tkagg \
    --exclude-module matplotlib.backends.backend_wxagg \
    --exclude-module matplotlib.backends.backend_gtk3agg \
    --exclude-module matplotlib.backends.backend_gtk4agg \
    --exclude-module tkinter \
    main.py

echo "Preparing DMG folder..."
mkdir -p dist/dmg
cp -r "dist/EBU R 128 Scanner.app" dist/dmg/
cp README_macOS.txt dist/dmg/
ln -s /Applications dist/dmg/Applications

echo "Creating DMG..."
hdiutil create -volname "EBU R 128 Scanner" -srcfolder dist/dmg -ov -format UDZO "EBU R 128 Scanner.dmg"

echo "Done! EBU R 128 Scanner.dmg is ready (Apple Silicon only)."
