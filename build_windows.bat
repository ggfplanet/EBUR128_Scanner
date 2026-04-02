@echo off
echo Cleaning old builds...
if exist build rd /s /q build
if exist dist rd /s /q dist

echo Building Windows application with PyInstaller...
:: Wir nutzen die gleichen Parameter wie im GitHub Workflow
python -m pip install -r requirements.txt

echo Initializing static_ffmpeg to ensure binaries are downloaded before packaging...
python -c "import static_ffmpeg; static_ffmpeg.add_paths()"

pyinstaller --noconfirm --onedir --windowed --icon="logo_tim/EBUR128_scanner_icon-macOS-Default-1024x1024@1x.png" --collect-all static_ffmpeg --name "EBUR128Scanner" main.py
echo.
echo If you have Inno Setup installed, you can now compile the installer:
echo Running ISCC...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_windows.iss

echo.
echo Done! The Windows installer should be in dist\installer\
pause
