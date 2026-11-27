# EBU R 128 Scanner

<p align="center">
  <img src="assets/EBUR128_scanner_icon-macOS-Default-1024x1024@1x.png" alt="EBU R 128 Scanner Icon" width="128" height="128">
</p>

<p align="center">
  <strong>Broadcast-grade loudness analysis for audio and video files according to EBU R 128 &amp; ITU-R BS.1770</strong><br>
  Available for <strong>macOS (Apple Silicon)</strong>, <strong>Windows (64-bit)</strong>, and <strong>Linux (x64 &amp; ARM64)</strong>
</p>

<p align="center">
  <a href="https://ggfplanet.de/ebur128scanner">Official Website &amp; Download</a> ·
  <a href="https://github.com/ggfplanet/EBUR128_Scanner/issues">Report Issue</a> ·
  <a href="LICENSE">GPL-3.0 License</a>
</p>

---

**EBU R 128 Scanner** measures the loudness of audio and video files according to **EBU Tech 3341 / 3342** and **ITU-R BS.1770**, calculating the exact gain adjustment in `dB` required to hit the **-23.0 LUFS** broadcast target. It clusters all True-Peak exceedances (`> -1.0 dBTP`) into timecoded events, plots the Short-Term loudness curve over time, and exports print-ready A4 PDF reports or plain-text summaries to the clipboard.

## Table of Contents

- [Key Features](#-key-features)
- [Quick Installation (End Users)](#-quick-installation-end-users)
- [Tech Stack](#-tech-stack)
- [Architecture & Project Structure](#-architecture--project-structure)
- [Getting Started (Local Development)](#-getting-started-local-development)
- [Testing](#-testing)
- [Building & Packaging](#-building--packaging)
- [Troubleshooting](#-troubleshooting)
- [Author, Credits & License](#-author-credits--license)

---

## ✨ Key Features

- **Integrated Loudness (`I`) & Gain Adjustment:** Measures integrated program loudness in `LUFS` and highlights the recommended gain correction toward `-23.0 LUFS` in green (`±1.0 LU` tolerance) or red.
- **True Peak (`Max`) & Event Clustering:** Detects peaks exceeding `-1.0 dBTP` and groups adjacent 100 ms frames into readable ranges with start/end timecodes (`hh:mm:ss`), duration, and peak value.
- **Loudness Range (`LRA`):** Reports program dynamic range in `LU`.
- **Short-Term Loudness Graph:** Plots loudness over time on the EBU +18 scale (`-60` to `+3 LUFS`) with `-23 LUFS` reference line and marked True-Peak exceedances.
- **A4 PDF Report Export:** Generates publication-grade 300 DPI PDF reports featuring header/app logo, file metadata, compliance badge, KPI cards, print-optimized 300 DPI graph, and paginated True-Peak tables.
- **Copy Values to Clipboard:** Copies a clean, graph-free plain-text summary of all metrics and peak timecodes with one click.
- **Drag & Drop + Real-Time Progress:** Drop media files straight onto the window and track progress from `0–100%` with elapsed/total duration and instant cancellation.
- **Smart Multi-Track & Discrete Mono Merging:** Automatically selects unambiguous single-track or dual-mono stereo layouts, or prompts for track selection (merging 2 or 6 discrete mono channels via FFmpeg `amerge`).
- **Broad Format Support:** Handles `WAV`, `AIFF`, `MP3`, `FLAC`, `AAC`, `MOV`, `MP4`, `MKV`, broadcast `MXF`, and any container readable by FFmpeg.
- **Bilingual & Privacy-First:** Automatically follows OS language (**English** or **German**) with persistent settings; processes all media locally using bundled FFmpeg without uploads or telemetry.
- **Built-in Update Service:** Non-blocking background check against `version.json` with one-click in-place terminal updates.

---

## 🚀 Quick Installation (End Users)

Install or update with a single terminal command (automatically clears macOS Gatekeeper / Windows SmartScreen flags and creates desktop/menu entries):

### 🍏 macOS (Apple Silicon / arm64)
```bash
curl -fsSL https://ggfplanet.de/ebur128scanner/install.sh | bash
```

### 🪟 Windows (64-bit PowerShell)
```powershell
irm https://ggfplanet.de/ebur128scanner/install.ps1 | iex
```

### 🐧 Linux (x64 & ARM64)
```bash
curl -fsSL https://ggfplanet.de/ebur128scanner/install-linux.sh | bash
```

> **Offline Installation:** Standalone `.zip` archives for all platforms are available directly below the terminal commands on [ggfplanet.de/ebur128scanner](https://ggfplanet.de/ebur128scanner).

<details>
<summary><strong>Uninstall Commands (macOS, Windows, Linux)</strong></summary>

- **🍏 macOS:**
  ```bash
  rm -rf "/Applications/EBU R 128 Scanner.app" ~/Library/Application\ Support/EBU\ R\ 128\ Scanner
  ```
- **🪟 Windows (PowerShell):**
  ```powershell
  Stop-Process -Name EBUR128Scanner -ErrorAction SilentlyContinue; Remove-Item "$env:LOCALAPPDATA\Programs\EBUR128Scanner", "$HOME\Desktop\EBU R 128 Scanner.lnk", "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\EBU R 128 Scanner.lnk" -Recurse -Force -ErrorAction SilentlyContinue
  ```
- **🐧 Linux:**
  ```bash
  rm -rf ~/.local/share/ebur128scanner ~/.local/bin/ebur128scanner ~/.local/share/applications/ebur128scanner.desktop ~/.local/share/icons/hicolor/*/apps/ebur128scanner.png ~/.local/share/pixmaps/ebur128scanner.png && update-desktop-database ~/.local/share/applications 2>/dev/null
  ```
</details>

---

## 🧰 Tech Stack

| Component | Technology | Purpose |
| --------- | ---------- | ------- |
| **Language** | Python 3.10+ | Application & audio analysis orchestration |
| **GUI Framework** | PySide6 `6.7.0` (`QtWidgets`, `QtGui`, `QtSvg`) | Native cross-platform dark UI & 300 DPI PDF generation (`QPdfWriter`) |
| **Media Engine** | Static `FFmpeg` / `FFprobe` (`ebur128=peak=true`) | Stream inspection & EBU R 128 / ITU-R BS.1770 measurement |
| **Plotting** | `matplotlib` (`FigureCanvasQTAgg` & `FigureCanvasAgg`) | Live Short-Term curve in UI & 300 DPI chart rendering for PDF reports |
| **Typography** | `Plus Jakarta Sans` & `JetBrains Mono` (SIL OFL 1.1) | Embedded variable fonts across Qt UI, Matplotlib charts, and PDFs |
| **Icons** | Rune Icons (Apache-2.0) | Monochrome 24×24 SVG vector icons with HiDPI support |
| **Packaging & CI** | PyInstaller `6.4.0` + GitHub Actions | Standalone bundles for macOS (`arm64`), Windows (`x64`), Linux (`x64` / `arm64`) |

---

## 🏗️ Architecture & Project Structure

### Directory Structure

```text
├── main.py                      # Entry point, PATH setup, dummy stdio for windowed mode, crash log
├── core/
│   ├── scanner.py               # FFprobe stream discovery, duration extraction & standard layout detection
│   ├── analyzer.py              # FFmpeg ebur128 subprocess runner, real-time progress & peak clustering
│   ├── binary_helper.py         # Bundled ffmpeg/ffprobe lookup & Windows Zone.Identifier unblocking
│   ├── report_formatter.py      # Compliance evaluation, stream metadata summary & clipboard formatter
│   └── update_service.py        # Non-blocking version check & OS-aware in-place updater
├── ui/
│   ├── app.py                   # MainWindow, Drag & Drop, background threads, result view & export actions
│   ├── dialogs.py               # StreamSelectionDialog, SettingsDialog & InfoDialog
│   ├── plot_helper.py           # Shared Matplotlib renderers (dark live UI + 300 DPI light print chart)
│   ├── pdf_report.py            # A4 PDF report generator (QPdfWriter + QPainter, paginated peak table)
│   ├── resources.py             # Paths, local font registration, QPalette dark theme & stylesheets
│   ├── icon_helper.py           # Retina-ready SVG icon loader with dynamic stroke colors
│   ├── update_banner.py         # Dismissible in-app update banner
│   └── i18n.py                  # DE/EN translations, system locale detection & QSettings persistence
├── assets/
│   ├── fonts/                   # PlusJakartaSans-Variable.ttf & JetBrainsMono-Variable.ttf
│   ├── icons/                   # Local Rune SVG icons (settings, info, close, zap, file-text, copy, check)
│   ├── icon.icns / icon.ico     # macOS & Windows application icons
│   └── EBUR128_scanner_icon-macOS-Default-1024x1024@1x.png
├── tests/                       # Unit & UI test suite (unittest)
├── download_ffmpeg_mac.py       # Fetches static Apple Silicon FFmpeg/FFprobe binaries
├── download_ffmpeg_win.py       # Fetches static Windows x64 FFmpeg/FFprobe binaries
├── download_ffmpeg_linux.py     # Fetches static Linux x64/arm64 FFmpeg/FFprobe binaries
├── EBU R 128 Scanner.spec       # PyInstaller configuration for macOS .app bundle
├── requirements.txt             # Python dependencies
└── .github/workflows/build.yml  # Automated Windows & Linux (x64 + ARM64) builds & test CI
```

### Data Flow

1. **Stream Inspection (`core/scanner.py`):** `ffprobe -show_format -show_streams` extracts audio stream metadata and total media duration. If unambiguous (1 stream, or 2 discrete mono streams), analysis starts automatically; otherwise `StreamSelectionDialog` lets the user select tracks.
2. **Loudness Measurement (`core/analyzer.py`):** Runs `ffmpeg -filter_complex ebur128=peak=true` in a background thread. Line-by-line stderr parsing feeds the progress bar (`0–100%`), collects Short-Term (`S`) samples and True-Peak exceedances (`> -1.0 dBTP`), and parses the final `Summary:` block (`I`, `LRA`, `Peak`, `Gain = -23.0 - I`).
3. **Export (`core/report_formatter.py`, `ui/pdf_report.py`):** Formats results either as plain text for `QApplication.clipboard()` or renders a multi-page 300 DPI A4 PDF via `QPdfWriter`, `QPainter`, and `FigureCanvasAgg`.

---

## 💻 Getting Started (Local Development)

### Prerequisites

- **Python 3.10+** (including `venv` and `pip`)
- **macOS / Windows:** No extra system libraries needed.
- **Linux (Debian / Ubuntu / Raspberry Pi OS):** Install Qt6 X11/Wayland runtime libraries before running GUI or tests:
  ```bash
  sudo apt-get update && sudo apt-get install -y \
    libgl1 libegl1 libxkbcommon0 libxkbcommon-x11-0 libfontconfig1 libdbus-1-3 \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xfixes0
  ```

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ggfplanet/EBUR128_Scanner.git
   cd EBUR128_Scanner
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # macOS / Linux
   # or on Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   ```
3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Download static FFmpeg & FFprobe binaries** (optional if `ffmpeg`/`ffprobe` are already on `PATH`):
   ```bash
   python download_ffmpeg_mac.py                 # macOS (Apple Silicon)
   python download_ffmpeg_win.py                 # Windows (64-bit)
   python download_ffmpeg_linux.py --arch=x64    # Linux x64 (or --arch=arm64)
   ```
   > On Linux, `download_ffmpeg_linux.py` auto-detects `x64` vs. `arm64` when `--arch` is omitted.

5. **Run the application:**
   ```bash
   python main.py
   ```

---

## 🧪 Testing

The test suite uses Python's built-in `unittest` module and runs UI checks offscreen without requiring a display server on CI:

```bash
# macOS / Windows (native display available)
python -m unittest discover tests -v

# Headless Linux / CI environments
QT_QPA_PLATFORM=offscreen python -m unittest discover tests -v
```

| Test Module | Coverage |
| ----------- | -------- |
| `tests/test_core.py` | FFmpeg `Summary:` parsing, True-Peak event clustering, track auto-selection & duration formatting |
| `tests/test_report.py` | Compliance rules, DE/EN clipboard report formatting, single- & multi-page 300 DPI PDF generation, UI export buttons |
| `tests/test_ui_palette.py` | Gain color thresholds (`±1.0 LU`), progress bar formatting, Drag & Drop, font loading, WinError 4551 error formatting |
| `tests/test_i18n.py` | OS locale detection (`de`/`en`) and `QSettings` persistence |
| `tests/test_icon_helper.py` | Presence and HiDPI rendering of all local Rune SVG icons |
| `tests/test_binary_helper.py` | FFmpeg binary resolution and safe Windows `Zone.Identifier` unblocking |
| `tests/test_update_service.py` | SemVer comparison and fail-silent offline update check fallback |

---

## 📦 Building & Packaging

### Local Build (macOS `.app` Bundle)

Ensure static Apple Silicon binaries (`ffmpeg` and `ffprobe`) exist in the repository root, then run PyInstaller with the bundled spec:

```bash
python download_ffmpeg_mac.py
pyinstaller --noconfirm "EBU R 128 Scanner.spec"
```

The bundle is generated in `dist/EBU R 128 Scanner.app` (`bundle_identifier`: `de.ggfplanet.ebur128scanner`, `LSMinimumSystemVersion`: `12.0`).

### Automated CI Builds (Windows & Linux)

Pushes to `main` or manual `workflow_dispatch` triggers execute [`.github/workflows/build.yml`](.github/workflows/build.yml):
- **`build-windows` (`windows-latest`):** Runs unit tests, downloads static Win64 FFmpeg builds, and packages a `--onedir` PyInstaller bundle.
- **`build-linux-x64` & `build-linux-arm64`:** Build inside `python:3.10-bullseye` containers (glibc 2.31 baseline) to ensure compatibility across Ubuntu, Debian 12+, and Raspberry Pi OS Bookworm, preserving symlinks and stripping conflicting system C++/GPU shared libraries before zipping.

---

## 🔧 Troubleshooting

- **macOS Gatekeeper warning on manual `.zip` extraction:**
  If you extract a manually downloaded archive instead of using `install.sh`, run:
  ```bash
  xattr -cr "/Applications/EBU R 128 Scanner.app"
  ```
- **Windows Smart App Control / `WinError 4551`:**
  Downloaded `.exe` files may carry a Mark of the Web (`Zone.Identifier`). The app attempts automatic unblocking at startup via `unblock_bundled_binaries()`. If Windows policies still block `ffmpeg.exe` / `ffprobe.exe`, right-click each `.exe` → **Properties** → check **Unblock**, or install via the PowerShell one-liner.
- **Linux headless test or missing XCB plugin error:**
  Verify that `libxcb-cursor0` (plus the Qt dependencies listed under Prerequisites) is installed, and pass `QT_QPA_PLATFORM=offscreen` when running tests without an X11/Wayland session.

---

## 👤 Author, Credits & License

**Tim Butenschön**
- Website: [ggfplanet.de/ebur128scanner](https://ggfplanet.de/ebur128scanner)
- GitHub: [ggfplanet/EBUR128_Scanner](https://github.com/ggfplanet/EBUR128_Scanner)
- Contact: `webseite@timbutenschoen.de`

### Credits & Third-Party Licenses

This project is licensed under the **[GNU General Public License v3.0 (GPL-3.0)](LICENSE)**.

- **FFmpeg / FFprobe:** Used for media inspection and loudness measurement under the [GNU GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.html) (or LGPL v2.1+). Source code is available at [ffmpeg.org/download.html](https://ffmpeg.org/download.html).
- **UI Icons:** [Rune Icons](https://runeicons.com) (Copyright Rune Icons Team), licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
- **Fonts:** `Plus Jakarta Sans` and `JetBrains Mono`, licensed under the SIL Open Font License 1.1 (OFL).

---

*Based on technical specifications EBU Tech 3341, EBU Tech 3342, and ITU-R BS.1770.*
