; Inno Setup Script für EBU R 128 Scanner (Windows)
; Dieses Skript erstellt einen Installer für die "onedir" Version von PyInstaller.

[Setup]
AppId=EBUR128Scanner-Butenschoen-3341
AppName=EBU R 128 Scanner
AppVersion=1.3
AppPublisher=Tim Butenschön
AppPublisherURL=https://ggfplanet.de/ebur128scanner
AppSupportURL=https://github.com/ggfplanet/EBUR128_Scanner
AppUpdatesURL=https://ggfplanet.de/ebur128scanner
DefaultDirName={autopf}\EBU R 128 Scanner
DefaultGroupName=EBU R 128 Scanner
AllowNoIcons=yes
; Pfad zum Verzeichnis, in dem der fertige Installer abgelegt werden soll
OutputDir=dist/installer
OutputBaseFilename=EBU_R_128_Scanner_Setup_V1.3
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Kopiert alle Dateien aus dem PyInstaller "dist/EBU R 128 Scanner" Verzeichnis
Source: "dist\EBU R 128 Scanner\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\EBU R 128 Scanner"; Filename: "{app}\EBU R 128 Scanner.exe"
Name: "{autodesktop}\EBU R 128 Scanner"; Filename: "{app}\EBU R 128 Scanner.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\EBU R 128 Scanner.exe"; Description: "{cm:LaunchProgram,EBU R 128 Scanner}"; Flags: nowait postinstall skipfsentry
