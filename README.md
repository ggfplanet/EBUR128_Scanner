# EBU R 128 Scanner

<p align="center">
  <img src="assets/EBUR128_scanner_icon-macOS-Default-1024x1024@1x.png" alt="EBU R 128 Scanner Icon" width="128" height="128">
</p>

<p align="center">
  <strong>Präzise Lautheitsanalyse für Audio- und Videodateien gemäß EBU R 128 &amp; ITU-R BS.1770</strong><br>
  Verfügbar für <strong>macOS (Apple Silicon)</strong> und <strong>Windows (64-Bit)</strong>
</p>

<p align="center">
  <a href="https://ggfplanet.de/ebur128scanner">Offizielle Webseite &amp; Download</a> ·
  <a href="https://github.com/ggfplanet/EBUR128_Scanner/issues">Fehler melden</a>
</p>

---

Der **EBU R 128 Scanner** misst die Lautheit von Audio- und Videodateien nach den technischen Empfehlungen **EBU Tech 3341 / 3342** und berechnet sofort, um wie viel dB der Pegel für den Zielwert von **-23.0 LUFS** angepasst werden muss. Zudem werden sämtliche True-Peak-Überschreitungen (`> -1.0 dBTP`) zeitgenau mit Timecodes aufgelistet und der Lautheitsverlauf grafisch dargestellt.

---

## 🚀 Schnell-Installation (Für Anwender)

Die einfachste Installation (sowie spätere Aktualisierung) erfolgt über einen einzigen Befehl im Terminal bzw. in der PowerShell. Dabei werden Gatekeeper- bzw. SmartScreen-Sperren automatisch bereinigt:

### 🍏 macOS (Apple Silicon / arm64)
Öffne die **Terminal**-App und führe folgenden Befehl aus:
```bash
curl -fsSL https://ggfplanet.de/ebur128scanner/install.sh | bash
```

### 🪟 Windows (64-Bit)
Öffne **Windows PowerShell** und führe folgenden Befehl aus:
```powershell
irm https://ggfplanet.de/ebur128scanner/install.ps1 | iex
```

> **Offline-Installation:** Auf der [offiziellen Projektseite (ggfplanet.de/ebur128scanner)](https://ggfplanet.de/ebur128scanner) stehen unterhalb der Terminal-Befehle auch direkte `.zip`-Archive für die manuelle Installation auf Offline-Systemen bereit.

<details>
<summary><strong>Hinweis für manuelle Offline-Installation unter macOS (Gatekeeper)</strong></summary>

Wenn du das `.zip`-Archiv manuell über den Browser herunterlädst statt den `curl`-Befehl zu nutzen, blockiert macOS unsignierte Apps beim ersten Start unter Umständen:
1. Entpacke `EBU R 128 Scanner.app` in deinen `/Applications` (Programme) Ordner.
2. Klicke mit der **rechten Maustaste** (oder `Ctrl`-Klick) auf die App und wähle **„Öffnen“** (oder erlaube den Start unter *Systemeinstellungen → Datenschutz & Sicherheit → „Dennoch öffnen“*).
3. Alternativ im Terminal: `xattr -cr "/Applications/EBU R 128 Scanner.app"`
</details>

---

## ✨ Features

- **Integrated Loudness (I):** Gesamtlautheit in `LUFS` (Zielwert: `-23.0 LUFS`).
- **Gain-Anpassungsvorschlag:** Sofortige Anzeige der nötigen Pegelkorrektur in `dB`.
- **True Peak (Max) & Event-Clustering:** Messung in `dBTP` inkl. automatischer Gruppierung von Überschreitungen (`> -1.0 dBTP`) mit exakten Start-/End-Timecodes und Dauer.
- **Loudness Range (LRA):** Messung der Dynamikspreizung in `LU`.
- **Grafischer Lautheitsverlauf:** Short-Term-Lautheitskurve auf der EBU +18 Skala (`-60` bis `+3 LUFS`) mit markierten True-Peak-Spitzen.
- **Intelligente Mehrkanal- & Spurauswahl:** Automatische Erkennung von Standard-Layouts (Stereo, 5.1, Dual-Mono) oder manuelle Auswahl einzelner Spuren bzw. kompatibler Mono-Paare (`amerge`).
- **Breite Formatunterstützung:** Unterstützt u. a. `WAV`, `AIFF`, `MP3`, `FLAC`, `AAC`, `MOV`, `MP4`, `MKV` sowie Broadcast-Container wie `MXF`.
- **1-Klick Update-System:** Integrierte, nicht-blockierende Update-Prüfung mit direktem In-Place-Update.
- **Zweisprachig:** Benutzeroberfläche jederzeit zwischen **Deutsch** und **Englisch** umschaltbar.

---

## 🛠️ Für Entwickler (Aus Quellcode starten)

### Voraussetzungen
- **Python 3.10+**
- **FFmpeg & FFprobe** (im System-`PATH` oder über die mitgelieferten Download-Skripte)

### Lokale Einrichtung
1. Repository klonen:
   ```bash
   git clone https://github.com/ggfplanet/EBUR128_Scanner.git
   cd EBUR128_Scanner
   ```
2. Virtuelle Umgebung erstellen und aktivieren:
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # macOS / Linux
   # oder unter Windows:
   venv\Scripts\activate
   ```
3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
4. Statische FFmpeg-Binaries herunterladen (optional, falls nicht global installiert):
   ```bash
   python download_ffmpeg_mac.py   # macOS (Apple Silicon)
   # oder
   python download_ffmpeg_win.py   # Windows (64-Bit)
   ```
5. Anwendung starten:
   ```bash
   python main.py
   ```

### Unit-Tests ausführen
```bash
python -m unittest discover tests
```

---

## 👤 Ersteller

**Tim Butenschön**
- Webseite: [ggfplanet.de/ebur128scanner](https://ggfplanet.de/ebur128scanner)
- GitHub: [ggfplanet/EBUR128_Scanner](https://github.com/ggfplanet/EBUR128_Scanner)
- Kontakt: webseite@timbutenschoen.de

## 📜 Credits & Lizenzen

Dieses Projekt steht unter der [GNU General Public License v3.0 (GPL-3.0)](LICENSE).
- **FFmpeg:** Nutzt [FFmpeg](https://ffmpeg.org) für die Medien- und Lautheitsanalyse unter der [GNU GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.html) (bzw. LGPL v2.1+). Der Quellcode ist auf [ffmpeg.org/download.html](https://ffmpeg.org/download.html) verfügbar.
- **UI-Icons:** UI-Icons stammen von [Rune Icons](https://runeicons.com) unter der [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) (Copyright Rune Icons Team).

---
*Basiert auf den technischen Empfehlungen EBU Tech 3341, EBU Tech 3342 und ITU-R BS.1770.*
