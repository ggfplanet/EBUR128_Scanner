import sys
import threading
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
                               QDialog, QCheckBox, QScrollArea, QComboBox, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QPalette, QColor, QFont, QIcon
import os

from core.scanner import get_audio_streams, is_standard_layout
from core.analyzer import analyze_loudness

import importlib.util
MATPLOTLIB_AVAILABLE = importlib.util.find_spec("matplotlib") is not None

VERSION = "1.3"

TRANSLATIONS = {
    "de": {
        "app_title": f"EBU R 128 Scanner V{VERSION}",
        "header": "Lautheitsanalyse (EBU R 128)",
        "info_text": "Wähle eine Audio- oder Videodatei aus, um die Lautheit zu messen.",
        "select_file": "Datei Auswählen",
        "reading_structure": "Dateistruktur wird gelesen...",
        "no_audio": "Keine Audiospuren gefunden oder Datei konnte nicht gelesen werden.",
        "standard_layout": "Standard-Layout erkannt. Analysiere...",
        "analyzing_tracks": "Analysiere {} Spur(en)...",
        "analyzing_time": "Analysiere Film-Zeit: {:.1f}s",
        "analysis_done": "Analyse abgeschlossen.",
        "analysis_failed": "Analyse fehlgeschlagen (FFmpeg gab keine Lautheits-Daten aus).",
        "gain_adjustment": "Anpassung: {}{} dB",
        "warning_peak": "Warnung: True-Peak (> -1 dBTP) überschritten ({}x)!",
        "adv_down": "Erweitert ▼",
        "adv_up": "Erweitert ▲",
        "i_label": "Integrated (I): {} LUFS",
        "lra_label": "Loudness Range (LRA): {} LU",
        "tp_label": "True Peak (Max): {} dBTP",
        "file_label": "Datei: {}",
        "error": "Fehler",
        "stream_sel_title": "Spurenauswahl",
        "stream_sel_info": "Audio-Layout weicht vom Standard ab.\nBitte wähle die zu messenden Spuren:",
        "track": "Spur {}",
        "channel_codec": "({} Kanal, {})",
        "analyze": "Analysieren",
        "select_at_least_one": "Bitte mindestens eine Spur auswählen!",
        "select_exactly_two": "Bitte genau 2 Spuren auswählen!",
        "file_dialog": "Datei auswählen",
        "media_files": "Media Files (*.*)",
        "creator_info": "Ersteller: Tim Butenschön<br><a href='https://ggfplanet.de/ebur128scanner' style='color: #2a82da;'>ggfplanet.de/ebur128scanner</a><br><a href='https://github.com/ggfplanet/EBUR128_Scanner' style='color: #2a82da;'>GitHub Projekt</a><br>webseite@timbutenschoen.de",
        "settings_title": "Einstellungen",
        "language": "Sprache:",
        "close": "Schließen",
        "legend_s": "Short-Term (S)",
        "legend_target": "Ziel (-23 LUFS)",
        "legend_peak": "Peak (> -1 dBTP)"
    },
    "en": {
        "app_title": f"EBU R 128 Scanner V{VERSION}",
        "header": "Loudness Analysis (EBU R 128)",
        "info_text": "Select an audio or video file to measure loudness.",
        "select_file": "Select File",
        "reading_structure": "Reading file structure...",
        "no_audio": "No audio tracks found or file could not be read.",
        "standard_layout": "Standard layout detected. Analyzing...",
        "analyzing_tracks": "Analyzing {} track(s)...",
        "analyzing_time": "Analyzing movie time: {:.1f}s",
        "analysis_done": "Analysis complete.",
        "analysis_failed": "Analysis failed (FFmpeg returned no loudness data).",
        "gain_adjustment": "Adjustment: {}{} dB",
        "warning_peak": "Warning: True-Peak (> -1 dBTP) exceeded ({}t)!",
        "adv_down": "Advanced ▼",
        "adv_up": "Advanced ▲",
        "i_label": "Integrated (I): {} LUFS",
        "lra_label": "Loudness Range (LRA): {} LU",
        "tp_label": "True Peak (Max): {} dBTP",
        "file_label": "File: {}",
        "error": "Error",
        "stream_sel_title": "Track Selection",
        "stream_sel_info": "Audio layout deviates from standard.\nPlease select the tracks to measure:",
        "track": "Track {}",
        "channel_codec": "({} channel, {})",
        "analyze": "Analyze",
        "select_at_least_one": "Please select at least one track!",
        "select_exactly_two": "Please select exactly 2 tracks!",
        "file_dialog": "Select File",
        "media_files": "Media Files (*.*)",
        "creator_info": "Creator: Tim Butenschön<br><a href='https://ggfplanet.de/ebur128scanner' style='color: #2a82da;'>ggfplanet.de/ebur128scanner</a><br><a href='https://github.com/ggfplanet/EBUR128_Scanner' style='color: #2a82da;'>GitHub Project</a><br>webseite@timbutenschoen.de",
        "settings_title": "Settings",
        "language": "Language:",
        "close": "Close",
        "legend_s": "Short-Term (S)",
        "legend_target": "Target (-23 LUFS)",
        "legend_peak": "Peak (> -1 dBTP)"
    }
}

CURRENT_LANG = "de"

def tr(key, *args):
    text = TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["de"]).get(key, key)
    if args:
        return text.format(*args)
    return text

class WorkerSignals(QObject):
    progress = Signal(float)
    finished_probe = Signal(list)
    finished_analyze = Signal(dict)
    error = Signal(str)

class StreamSelectionDialog(QDialog):
    def __init__(self, streams, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("stream_sel_title"))
        self.setFixedSize(450, 350)
        self.selected_indices = []
        
        layout = QVBoxLayout(self)
        
        self.info_label = QLabel(tr("stream_sel_info"))
        self.info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.info_label)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        
        self.checkboxes = []
        for i, s in enumerate(streams):
            idx = s["audio_index"]
            ch = s.get("channels", "?")
            codec = s.get("codec_name", "")
            title = s.get("tags", {}).get("title", f"{tr('track', idx+1)}")
            
            cb = QCheckBox(f"{title} {tr('channel_codec', ch, codec)}")
            cb.setProperty("stream_index", idx)
            if i < 2:
                cb.setChecked(True)
            self.checkboxes.append(cb)
            self.scroll_layout.addWidget(cb)
            
        self.scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self.btn = QPushButton(tr("analyze"))
        self.btn.clicked.connect(self.on_submit)
        self.btn.setMinimumHeight(40)
        layout.addWidget(self.btn)
        
    def on_submit(self):
        self.selected_indices = [cb.property("stream_index") for cb in self.checkboxes if cb.isChecked()]
        if len(self.checkboxes) >= 2 and len(self.selected_indices) != 2:
            QMessageBox.warning(self, tr("error"), tr("select_exactly_two"))
            return
        elif not self.selected_indices:
            QMessageBox.warning(self, tr("error"), tr("select_at_least_one"))
            return
        self.accept()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle(tr("settings_title"))
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout(self)
        
        lang_layout = QHBoxLayout()
        lang_label = QLabel(tr("language"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Deutsch", "de")
        self.lang_combo.addItem("English", "en")
        
        idx = 0 if CURRENT_LANG == "de" else 1
        self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)
        
        layout.addStretch()
        
        close_btn = QPushButton(tr("close"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def change_language(self):
        global CURRENT_LANG
        CURRENT_LANG = self.lang_combo.currentData()
        self.setWindowTitle(tr("settings_title"))
        if self.parent_window:
            self.parent_window.update_texts()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(600, 650)
        
        # Signals for threads
        self.signals = WorkerSignals()
        self.signals.progress.connect(self.update_progress)
        self.signals.finished_probe.connect(self.on_probe_done)
        self.signals.finished_analyze.connect(self.on_analyze_done)
        self.signals.error.connect(self.on_error)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 10)
        
        # Header
        self.header_label = QLabel()
        self.header_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.header_label)

        self.info_label = QLabel()
        self.info_label.setStyleSheet("font-size: 14px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.info_label)
        self.main_layout.addSpacing(20)

        # Action Area
        self.action_widget = QWidget()
        self.action_layout = QVBoxLayout(self.action_widget)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        
        self.select_btn = QPushButton()
        self.select_btn.setMinimumHeight(50)
        self.select_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.select_btn.clicked.connect(self.open_file)
        self.action_layout.addWidget(self.select_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.progress_bar.hide()
        self.action_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.action_layout.addWidget(self.status_label)
        
        self.main_layout.addWidget(self.action_widget)
        
        # Results Area
        self.result_widget = QWidget()
        self.result_layout = QVBoxLayout(self.result_widget)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_widget.hide()
        
        self.gain_label = QLabel("")
        self.gain_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.gain_label.setAlignment(Qt.AlignCenter)
        self.result_layout.addWidget(self.gain_label)
        
        self.alert_label = QLabel("")
        self.alert_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff5555;")
        self.alert_label.setAlignment(Qt.AlignCenter)
        self.result_layout.addWidget(self.alert_label)
        
        self.timecodes_textbox = QTextEdit()
        self.timecodes_textbox.setMaximumHeight(80)
        self.timecodes_textbox.setReadOnly(True)
        self.result_layout.addWidget(self.timecodes_textbox)
        
        self.adv_btn = QPushButton()
        self.adv_btn.setFlat(True)
        self.adv_btn.clicked.connect(self.toggle_advanced)
        self.result_layout.addWidget(self.adv_btn)
        
        self.adv_widget = QWidget()
        self.adv_layout = QVBoxLayout(self.adv_widget)
        
        self.i_label = QLabel()
        self.lra_label = QLabel()
        self.tp_label = QLabel()
        self.file_label = QLabel()
        
        for lbl in (self.i_label, self.lra_label, self.tp_label, self.file_label):
            lbl.setStyleSheet("font-size: 14px;")
            self.adv_layout.addWidget(lbl)
            
        self.adv_widget.hide()
        
        # Plot for loudness over time
        if MATPLOTLIB_AVAILABLE:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            self.figure = Figure(figsize=(5, 3), facecolor='#282828')
            self.canvas = FigureCanvas(self.figure)
            self.ax = self.figure.subplots()
            self._setup_plot_style()
            self.adv_layout.addWidget(self.canvas)
        
        self.result_layout.addWidget(self.adv_widget)
        
        self.main_layout.addWidget(self.result_widget)
        self.main_layout.addStretch()

        # Bottom Bar: VERSION, info, settings
        bottom_layout = QHBoxLayout()
        v_label = QLabel(f"V{VERSION}")
        v_label.setStyleSheet("color: #777777; font-size: 10px;")
        
        info_btn = QPushButton("i")
        info_btn.setFixedSize(16, 16)
        info_btn.setStyleSheet("border-radius: 8px; border: 1px solid #777777; color: #777777; font-size: 10px; font-style: italic;")
        info_btn.clicked.connect(self.show_info)

        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setStyleSheet("border: none; color: #777777; font-size: 24px;")
        settings_btn.clicked.connect(self.show_settings)

        bottom_layout.addWidget(v_label)
        bottom_layout.addWidget(info_btn)
        bottom_layout.addWidget(settings_btn)
        bottom_layout.addStretch()

        self.main_layout.addLayout(bottom_layout)
        
        self.current_file = None
        self.current_result = None

        self.update_texts()

    def _setup_plot_style(self):
        if not MATPLOTLIB_AVAILABLE: return
        self.ax.set_facecolor('#282828')
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.set_xlabel("Time (s)", color='white', fontsize=9)
        self.ax.set_ylabel("LUFS", color='white', fontsize=9)
        self.ax.grid(True, alpha=0.2, color='white')
        self.figure.tight_layout()

    def update_texts(self):
        self.setWindowTitle(tr("app_title"))
        self.header_label.setText(tr("header"))
        self.info_label.setText(tr("info_text"))
        self.select_btn.setText(tr("select_file"))
        if self.adv_widget.isHidden():
            self.adv_btn.setText(tr("adv_down"))
        else:
            self.adv_btn.setText(tr("adv_up"))

        # Redraw result if present
        if self.current_result:
            self._display_result(self.current_result)
        else:
            self.i_label.setText(tr("i_label", "-"))
            self.lra_label.setText(tr("lra_label", "-"))
            self.tp_label.setText(tr("tp_label", "-"))
            self.file_label.setText(tr("file_label", "..."))

    def show_info(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Info (V{VERSION})")
        msg.setTextFormat(Qt.RichText)
        msg.setText(tr("creator_info"))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def show_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def toggle_advanced(self):
        if self.adv_widget.isHidden():
            self.adv_widget.show()
            self.adv_btn.setText(tr("adv_up"))
        else:
            self.adv_widget.hide()
            self.adv_btn.setText(tr("adv_down"))

    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, tr("file_dialog"), "", tr("media_files"))
        if filepath:
            self.current_file = filepath
            self.start_analysis_flow()

    def set_loading(self, loading, text=""):
        if loading:
            self.select_btn.setEnabled(False)
            self.progress_bar.show()
            self.status_label.setText(text)
            self.result_widget.hide()
            self.alert_label.hide()
            self.timecodes_textbox.hide()
        else:
            self.select_btn.setEnabled(True)
            self.progress_bar.hide()
            self.status_label.setText(text)

    def start_analysis_flow(self):
        self.set_loading(True, tr("reading_structure"))
        threading.Thread(target=self._probe_thread, daemon=True).start()

    def _probe_thread(self):
        try:
            streams = get_audio_streams(self.current_file)
            self.signals.finished_probe.emit(streams)
        except Exception as e:
            self.signals.error.emit(str(e))

    def on_error(self, message):
        self.set_loading(False, "")
        QMessageBox.critical(self, tr("error"), message)

    def on_probe_done(self, streams):
        if not streams:
            self.on_error(tr("no_audio"))
            return

        if is_standard_layout(streams):
            self.status_label.setText(tr("standard_layout"))
            selected = [s["audio_index"] for s in streams[:3]]
            self._start_ffmpeg_analysis(selected)
        else:
            self.set_loading(False, "")
            dlg = StreamSelectionDialog(streams, self)
            if dlg.exec():
                self.set_loading(True, tr("analyzing_tracks", len(dlg.selected_indices)))
                self._start_ffmpeg_analysis(dlg.selected_indices)

    def _start_ffmpeg_analysis(self, stream_indices):
        threading.Thread(target=self._analyze_thread, args=(stream_indices,), daemon=True).start()

    def _analyze_thread(self, stream_indices):
        def progress_cb(t):
            self.signals.progress.emit(t)
            
        try:
            result = analyze_loudness(self.current_file, stream_indices, progress_callback=progress_cb)
            self.signals.finished_analyze.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))

    def update_progress(self, t):
        self.status_label.setText(tr("analyzing_time", t))

    def on_analyze_done(self, result):
        self.set_loading(False, tr("analysis_done"))
        
        if result.get("I") is None:
            self.on_error(tr("analysis_failed"))
            return
            
        self.current_result = result
        self.result_widget.show()
        self._display_result(result)

    def _display_result(self, result):
        gain = result["Gain"]
        sign = "+" if gain >= 0 else ""
        self.gain_label.setText(tr("gain_adjustment", sign, gain))
        
        tc = result["Exceeded_Timecodes"]
        if tc:
            self.alert_label.show()
            self.alert_label.setText(tr("warning_peak", len(tc)))
            self.timecodes_textbox.show()
            self.timecodes_textbox.setText("\n".join(tc))
        else:
            self.alert_label.hide()
            self.timecodes_textbox.hide()
            
        i_val = "N/A" if result["I"] is None else result["I"]
        lra_val = "N/A" if result["LRA"] is None else result["LRA"]
        tp_val = "N/A" if result["Peak"] is None else result["Peak"]
        self.i_label.setText(tr("i_label", i_val))
        self.lra_label.setText(tr("lra_label", lra_val))
        self.tp_label.setText(tr("tp_label", tp_val))
        filename = os.path.basename(self.current_file) if self.current_file else "N/A"
        self.file_label.setText(tr("file_label", filename))

        # Update Plot
        if MATPLOTLIB_AVAILABLE:
            self.ax.clear()
            self._setup_plot_style()
            
            times = result.get("Time_Points", [])
            loudness = result.get("Loudness_Values", [])
            peaks = result.get("Peak_Exceedances", [])
            
            if times and loudness:
                self.ax.plot(times, loudness, color='#2a82da', linewidth=1.5, label=tr("legend_s"))
                
                if peaks:
                    px = [p[0] for p in peaks]
                    py = [p[1] for p in peaks]
                    self.ax.scatter(px, py, color='#ff5555', s=20, zorder=5, label=tr("legend_peak"))
                
                # Target Line
                self.ax.axhline(y=-23, color='#44aa44', linestyle='--', alpha=0.6, label=tr("legend_target"))
                
                self.ax.legend(loc="lower right", fontsize=8, facecolor="#282828", edgecolor="white", labelcolor="white")
                
                self.figure.tight_layout()
                self.canvas.draw()

def run_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logo_tim", "EBUR128_scanner_icon-macOS-Default-1024x1024@1x.png")
    app.setWindowIcon(QIcon(os.path.abspath(icon_path)))
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(40, 40, 40))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
