# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('ffmpeg', '.'), ('ffprobe', '.')],
    datas=[('assets', 'assets'), ('LICENSE', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'static_ffmpeg', 
        'PySide6.QtWebEngineCore', 
        'PySide6.QtWebEngineWidgets', 
        'PySide6.QtQml', 
        'PySide6.QtQuick', 
        'PySide6.QtSql', 
        'PySide6.QtXml', 
        'PySide6.QtTest', 
        'PySide6.QtDBus', 
        'PySide6.QtBluetooth', 
        'PySide6.QtNfc', 
        'PySide6.QtMultimedia', 
        'PySide6.QtPositioning', 
        'PySide6.QtLocation', 
        'PySide6.QtSensors', 
        'PySide6.QtSerialPort', 
        'matplotlib.backends.backend_tkagg', 
        'matplotlib.backends.backend_wxagg', 
        'matplotlib.backends.backend_gtk3agg', 
        'matplotlib.backends.backend_gtk4agg', 
        'tkinter'
    ],
    noarchive=False,
)

# Filter unwanted Qt frameworks, plugins, and resources
# NOTE: QtDBus is required by QtGui on macOS (otool shows QtGui hard-links @rpath/QtDBus)
UNWANTED_QT = (
    'QtWebEngine', 'QtWebEngineCore', 'QtWebEngineWidgets',
    'QtQuick', 'QtQuickWidgets', 'QtQuickControls2',
    'QtQml', 'QtQmlModels',
    'QtVirtualKeyboard', 'virtualkeyboard',
    'QtSql', 'QtTest', 'QtMultimedia', 'QtLocation', 'QtPositioning',
    'QtSensors', 'QtBluetooth', 'QtNfc', 'QtCharts', 'Qt3D',
    'QtGamepad', 'QtPdf', 'QtDataVisualization', 'QtRemoteObjects',
    'QtScxml', 'QtWebChannel', 'QtWebSockets', 'QtWebView',
)

a.binaries = [
    x for x in a.binaries 
    if not any(unwanted in x[0] or (isinstance(x[1], str) and unwanted in x[1]) for unwanted in UNWANTED_QT)
]

a.datas = [
    x for x in a.datas 
    if not any(unwanted in x[0] or (isinstance(x[1], str) and unwanted in x[1]) for unwanted in UNWANTED_QT)
]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EBU R 128 Scanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EBU R 128 Scanner',
)
app = BUNDLE(
    coll,
    name='EBU R 128 Scanner.app',
    icon='assets/icon.icns',
    bundle_identifier='de.ggfplanet.ebur128scanner',
    info_plist={
        'CFBundleName': 'EBU R 128 Scanner',
        'CFBundleDisplayName': 'EBU R 128 Scanner',
        'CFBundleIdentifier': 'de.ggfplanet.ebur128scanner',
        'CFBundleVersion': '1.5.2',
        'CFBundleShortVersionString': '1.5.2',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'LSMinimumSystemVersion': '12.0',
    }
)
