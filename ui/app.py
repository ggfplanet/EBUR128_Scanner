import sys
import threading
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
                               QDialog, QCheckBox, QScrollArea, QComboBox, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QPalette, QColor, QFont, QIcon
import os
import subprocess

from core.scanner import get_audio_streams, get_standard_selection
from core.analyzer import analyze_loudness, format_timecode

import importlib.util
MATPLOTLIB_AVAILABLE = importlib.util.find_spec("matplotlib") is not None

from ui.i18n import tr, VERSION
from ui.dialogs import StreamSelectionDialog, SettingsDialog, InfoDialog
from ui.update_banner import UpdateBanner
from core.update_service import check_for_updates


def format_user_error(e: Exception) -> str:
    """Übersetzt technische Exceptions in nutzerfreundliche Fehlermeldungen."""
    msg_str = str(e).lower()
    if isinstance(e, FileNotFoundError):
        if "ffmpeg" in msg_str or "ffprobe" in msg_str:
            return tr("error_ffmpeg_not_found")
        return tr("error_file_read")
    if isinstance(e, (subprocess.CalledProcessError, subprocess.SubprocessError, RuntimeError)):
        return tr("error_file_read")
    return tr("error_general", str(e))


def get_resource_path(relative_path: str) -> str:
    """Ermittelt den Pfad zu einer Ressource (funktioniert in Dev & gepacktem PyInstaller-Build)."""
    candidates = []
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.append(os.path.join(sys._MEIPASS, relative_path))
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, relative_path))
        candidates.append(os.path.join(exe_dir, "_internal", relative_path))
        candidates.append(os.path.normpath(os.path.join(exe_dir, "..", "Resources", relative_path)))
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.append(os.path.join(project_root, relative_path))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[0] if candidates else relative_path

class WorkerSignals(QObject):
    progress = Signal(float)
    finished_probe = Signal(list)
    finished_analyze = Signal(dict)
    error = Signal(str)
    update_checked = Signal(dict)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(600, 650)
        if not QApplication.windowIcon().isNull():
            self.setWindowIcon(QApplication.windowIcon())
        
        # Signals for threads
        self.signals = WorkerSignals()
        self.signals.progress.connect(self.update_progress)
        self.signals.finished_probe.connect(self.on_probe_done)
        self.signals.finished_analyze.connect(self.on_analyze_done)
        self.signals.error.connect(self.on_error)
        self.signals.update_checked.connect(self.on_update_checked)

        self.cancel_event = threading.Event()
        self.active_process = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 10)

        # Update Banner (tim-update)
        self.update_banner = UpdateBanner()
        self.main_layout.addWidget(self.update_banner)
        
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

        self.cancel_btn = QPushButton(tr("cancel"))
        self.cancel_btn.setMinimumHeight(32)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #383838;
                color: #e0e0e0;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 14px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #ff5555;
                color: #ffffff;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_analysis)
        self.cancel_btn.hide()
        self.action_layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)
        
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
        
        self.adv_widget = QWidget()
        self.adv_layout = QVBoxLayout(self.adv_widget)
        
        self.i_label = QLabel()
        self.lra_label = QLabel()
        self.tp_label = QLabel()
        self.file_label = QLabel()
        
        for lbl in (self.i_label, self.lra_label, self.tp_label, self.file_label):
            lbl.setStyleSheet("font-size: 14px;")
            self.adv_layout.addWidget(lbl)
        
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
        self._start_update_check()

    def _start_update_check(self):
        def _check():
            res = check_for_updates(VERSION)
            self.signals.update_checked.emit(res)
        threading.Thread(target=_check, daemon=True).start()

    def on_update_checked(self, result):
        if result and result.get("has_update"):
            self.update_banner.set_update_info(result)

    def _setup_plot_style(self):
        if not MATPLOTLIB_AVAILABLE: return
        self.ax.set_facecolor('#282828')
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.set_xlabel(tr("plot_time"), color='white', fontsize=9)
        self.ax.set_ylabel(tr("plot_lufs"), color='white', fontsize=9)
        self.ax.set_ylim(-60, 3)
        self.ax.grid(True, alpha=0.2, color='white')
        self.figure.tight_layout()

    def update_texts(self):
        self.setWindowTitle(tr("app_title"))
        self.header_label.setText(tr("header"))
        self.info_label.setText(tr("info_text"))
        self.select_btn.setText(tr("select_file"))
        self.cancel_btn.setText(tr("cancel"))

        if hasattr(self, 'update_banner'):
            self.update_banner.update_texts()

        # Redraw result if present
        if self.current_result:
            self._display_result(self.current_result)
        else:
            self.i_label.setText(tr("i_label", "-"))
            self.lra_label.setText(tr("lra_label", "-"))
            self.tp_label.setText(tr("tp_label", "-"))
            self.file_label.setText(tr("file_label", "..."))

    def show_info(self):
        dlg = InfoDialog(self)
        dlg.exec()

    def show_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, tr("file_dialog"), "", tr("media_files"))
        if filepath:
            self.current_file = filepath
            self.start_analysis_flow()

    def set_loading(self, loading, text=""):
        if loading:
            self.select_btn.setEnabled(False)
            self.progress_bar.show()
            self.cancel_btn.show()
            self.status_label.setText(text)
            self.result_widget.hide()
            self.alert_label.hide()
            self.timecodes_textbox.hide()
        else:
            self.select_btn.setEnabled(True)
            self.progress_bar.hide()
            self.cancel_btn.hide()
            self.status_label.setText(text)

    def start_analysis_flow(self):
        self.set_loading(True, tr("reading_structure"))
        threading.Thread(target=self._probe_thread, daemon=True).start()

    def _probe_thread(self):
        try:
            streams = get_audio_streams(self.current_file)
            self.signals.finished_probe.emit(streams)
        except Exception as e:
            self.signals.error.emit(format_user_error(e))

    def on_error(self, message):
        self.set_loading(False, "")
        QMessageBox.critical(self, tr("error"), message)

    def on_probe_done(self, streams):
        if not streams:
            self.on_error(tr("no_audio"))
            return

        standard_sel = get_standard_selection(streams)
        if standard_sel is not None:
            self.status_label.setText(tr("standard_layout"))
            self._start_ffmpeg_analysis(standard_sel)
        else:
            self.set_loading(False, "")
            dlg = StreamSelectionDialog(streams, self)
            if dlg.exec():
                self.set_loading(True, tr("analyzing_tracks", len(dlg.selected_indices)))
                self._start_ffmpeg_analysis(dlg.selected_indices)

    def _start_ffmpeg_analysis(self, stream_indices):
        self.cancel_event.clear()
        self.active_process = None
        threading.Thread(target=self._analyze_thread, args=(stream_indices,), daemon=True).start()

    def _analyze_thread(self, stream_indices):
        def progress_cb(t):
            self.signals.progress.emit(t)

        def on_started(proc):
            self.active_process = proc
            
        try:
            result = analyze_loudness(
                self.current_file, 
                stream_indices, 
                progress_callback=progress_cb,
                cancel_event=self.cancel_event,
                on_process_started=on_started
            )
            self.signals.finished_analyze.emit(result)
        except Exception as e:
            if not self.cancel_event.is_set():
                self.signals.error.emit(format_user_error(e))

    def cancel_analysis(self):
        self.cancel_event.set()
        if self.active_process:
            try:
                self.active_process.terminate()
                try:
                    self.active_process.wait(timeout=0.5)
                except Exception:
                    self.active_process.kill()
            except Exception:
                pass
        self.set_loading(False, tr("analysis_cancelled"))

    def update_progress(self, t):
        self.status_label.setText(tr("analyzing_time", t))

    def on_analyze_done(self, result):
        if self.cancel_event.is_set() or result.get("Cancelled"):
            self.set_loading(False, tr("analysis_cancelled"))
            return

        self.set_loading(False, tr("analysis_done"))
        
        if result.get("I") is None:
            self.on_error(tr("analysis_failed"))
            return
            
        self.current_result = result
        self.result_widget.show()
        self._display_result(result)

    def closeEvent(self, event):
        self.cancel_analysis()
        event.accept()

    def _display_result(self, result):
        gain = result["Gain"]
        sign = "+" if gain >= 0 else ""
        self.gain_label.setText(tr("gain_adjustment", sign, gain))
        
        events = result.get("Peak_Events", [])
        if events:
            self.alert_label.show()
            if len(events) == 1:
                self.alert_label.setText(tr("warning_peak_single"))
            else:
                self.alert_label.setText(tr("warning_peak_multi", len(events)))
            
            lines = []
            for ev in events:
                start_tc = format_timecode(ev["start"])
                sign_p = "+" if ev["max_peak"] >= 0 else ""
                peak_str = f"{sign_p}{ev['max_peak']:.1f} dBTP"
                dur = ev.get("duration", 0.0)
                if dur >= 0.3:
                    end_tc = format_timecode(ev["end"])
                    lines.append(tr("peak_event_range", start_tc, end_tc, dur, peak_str))
                else:
                    lines.append(tr("peak_event_point", start_tc, peak_str))
            
            self.timecodes_textbox.show()
            self.timecodes_textbox.setText("\n".join(lines))
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
                
                # EBU +18 scale: -60 LUFS to +3 LUFS headroom
                self.ax.set_ylim(-60, 3)
                
                self.ax.legend(loc="lower right", fontsize=8, facecolor="#282828", edgecolor="white", labelcolor="white")
                
                self.figure.tight_layout()
                self.canvas.draw()

def run_app():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("de.ggfplanet.ebur128scanner")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Icon laden (Windows: icon.ico bevorzugt, Fallback PNG)
    icon_rel = "assets/icon.ico" if sys.platform == "win32" and os.path.exists(get_resource_path("assets/icon.ico")) else "assets/EBUR128_scanner_icon-macOS-Default-1024x1024@1x.png"
    icon_path = get_resource_path(icon_rel)
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        if not icon.isNull():
            app.setWindowIcon(icon)
    
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
