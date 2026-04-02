# EBU R 128 Scanner

Ein Tool zur Loudness-Analyse von Audio- und Videodateien gemäß der EBU-Empfehlung R 128.

Der **EBU R 128 Scanner** ermöglicht eine präzise Messung der Lautheit von Mediendateien, um sicherzustellen, dass diese den gängigen Aussteuerungs-Standards entsprechen. Er bietet Unterstützung für die Analyse einzelner oder mehrerer Audiospuren und berechnet die notwendige Pegelanpassung an den Zielwert von -23 LUFS.

## Features
- **Integrated Loudness (I):** Messung der Gesamtlautheit in LUFS.
- **Loudness Range (LRA):** Analyse der Dynamikspreizung in LU.
- **True Peak (Max):** Erfassung des maximalen True-Peak-Pegels in dBTP.
- **Anpassungs-Vorschlag:** Automatische Berechnung des Gain-Offsets für die Normalisierung auf -23 LUFS.
- **Spurauswahl:** Automatisches Erkennen von Standardlayouts oder manuelle Auswahl der zu messenden Audiospuren.
- **Plattformübergreifend:** Verfügbar für Windows und macOS.
- **Zweisprachig:** Benutzeroberfläche in Deutsch und Englisch.

## Anforderungen
- **Python 3.10+**
- **FFmpeg:** Das Tool nutzt FFmpeg für die Audioanalyse. Stellen Sie sicher, dass `ffmpeg` in Ihrem Systempfad installiert ist.

## Installation
1. Repository klonen:
   ```bash
   git clone https://github.com/ggfplanet/EBUR128_Scanner.git
   cd EBUR128_Scanner
   ```
2. Virtuelle Umgebung erstellen (optional):
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # oder
   venv\Scripts\activate     # Windows
   ```
3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```

## Nutzung
Starten Sie die Applikation über das Hauptskript:
```bash
python main.py
```
Oder nutzen Sie auf macOS das bereitgestellte Start-Skript:
```bash
./Start_Scanner.command
```

## Build-Informationen
### macOS
Ein DMG-Installer kann mit dem bereitgestellten Skript erstellt werden:
```bash
./build_dmg.sh
```
Dies nutzt `PyInstaller` und `hdiutil`, um ein fertiges Installationsimage zu erzeugen. 
*Hinweis: Das Skript ist ab V1.3 für Apple Silicon (arm64) optimiert, um die Dateigröße gering zu halten. Unterstützung für Intel Macs ist nicht mehr enthalten.*

### Windows
Die Erstellung der Windows-Executable (`.exe`) erfolgt automatisiert über GitHub Actions (siehe `.github/workflows/build.yml`) bei jedem Push auf den `main`-Branch.

## Ersteller
**Tim Butenschön**
- Webseite: [ggfplanet.de/ebur128scanner](https://ggfplanet.de/ebur128scanner)
- GitHub: [ggfplanet/EBUR128_Scanner](https://github.com/ggfplanet/EBUR128_Scanner)
- Kontakt: webseite@timbutenschoen.de

---
*Basiert auf den technischen Empfehlungen EBU Tech 3341 und Tech 3342.*
