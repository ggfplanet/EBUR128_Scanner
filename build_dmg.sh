#!/bin/bash
set -e
cd "$(dirname "$0")"

# Fallback to CommandLineTools if Xcode license is unaccepted
if [ -d "/Library/Developer/CommandLineTools" ]; then
    export DEVELOPER_DIR="/Library/Developer/CommandLineTools"
fi

echo "Cleaning old builds..."
rm -rf build dist "EBU R 128 Scanner.dmg" "EBU_R_128_Scanner_v1.3.dmg" "EBU_R_128_Scanner_v1.4.0.dmg"

echo "Ensuring native Apple Silicon FFmpeg binaries are available..."
./venv/bin/python3 download_ffmpeg_mac.py

echo "Building Mac application with PyInstaller from spec (Apple Silicon only)..."
./venv/bin/python3 -m PyInstaller --noconfirm "EBU R 128 Scanner.spec"

echo "Preparing DMG folder..."
mkdir -p dist/dmg
ditto "dist/EBU R 128 Scanner.app" "dist/dmg/EBU R 128 Scanner.app"
cp README_macOS.txt dist/dmg/

echo "Ensuring macOS Bundle metadata in Info.plist..."
PLIST="dist/dmg/EBU R 128 Scanner.app/Contents/Info.plist"
if [ -f "$PLIST" ]; then
    /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier de.ggfplanet.ebur128scanner" "$PLIST" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string de.ggfplanet.ebur128scanner" "$PLIST"
    /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString 1.4.0" "$PLIST" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string 1.4.0" "$PLIST"
    /usr/libexec/PlistBuddy -c "Set :CFBundleVersion 1.4.0" "$PLIST" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string 1.4.0" "$PLIST"
fi

echo "Cleaning up unneeded frameworks to reduce size..."
# Wir entfernen manuell schwere, nicht genutzte Qt-Frameworks aus dem Bundle
FRAMEWORKS_DIR="dist/dmg/EBU R 128 Scanner.app/Contents/Frameworks"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtWebEngineCore.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtWebEngineWidgets.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtQuick.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtQml.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtVirtualKeyboard.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtSql.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtTest.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtMultimedia.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtLocation.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtPositioning.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtSensors.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtBluetooth.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtNfc.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtCharts.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/Qt3DCore.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/Qt3DRender.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtGamepad.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtPdf.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtDataVisualization.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtRemoteObjects.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtScxml.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtWebChannel.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtWebSockets.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtWebView.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtQuickControls2.framework"
rm -rf "$FRAMEWORKS_DIR/PySide6/Qt/lib/QtQuickWidgets.framework"

echo "Cleaning up broken symlinks..."
APP_BUNDLE="dist/dmg/EBU R 128 Scanner.app"
find "$APP_BUNDLE" -type l -exec sh -c 'for x; do [ -e "$x" ] || rm -f "$x"; done' _ {} +

echo "Signing application bundle ad-hoc (Gatekeeper optimization)..."
xattr -cr "$APP_BUNDLE"
codesign --force --deep -s - "$APP_BUNDLE"
codesign -vvv --deep --strict "$APP_BUNDLE"

ln -s /Applications dist/dmg/Applications

echo "Creating DMG..."
hdiutil create -volname "EBU R 128 Scanner" -srcfolder dist/dmg -ov -format UDZO "EBU_R_128_Scanner_v1.4.0.dmg"

echo "Done! EBU_R_128_Scanner_v1.4.0.dmg is ready (Apple Silicon only)."
