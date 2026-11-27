import sys
import threading
import os
import importlib.util
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QObject, QSize, QTimer

from core.scanner import get_audio_streams, get_standard_selection, extract_duration, format_short_time
from core.analyzer import analyze_loudness
from core.report_formatter import (
    build_clipboard_report, format_peak_event_line, format_stream_summary, suggest_pdf_filename
)

MATPLOTLIB_AVAILABLE = importlib.util.find_spec("matplotlib") is not None

from ui.i18n import tr, VERSION, init_language
from ui.dialogs import StreamSelectionDialog, SettingsDialog, InfoDialog
from ui.pdf_report import generate_pdf_report
from ui.plot_helper import draw_dark_loudness_plot, setup_dark_plot_axes
from ui.update_banner import UpdateBanner
from ui.icon_helper import get_rune_icon
from ui.resources import (
    format_user_error, init_fonts, setup_app_theme,
    SELECT_BTN_STYLE, SELECT_BTN_DRAG_STYLE, PROGRESS_BAR_STYLE,
    CANCEL_BTN_STYLE, DEV_INFO_BTN_STYLE,
    REPORT_BTN_PRIMARY_STYLE, REPORT_BTN_SECONDARY_STYLE, REPORT_BTN_SUCCESS_STYLE,
)
from core.update_service import check_for_updates


class WorkerSignals(QObject):
    progress = Signal(float)
    finished_probe = Signal(list)
    finished_analyze = Signal(dict)
    error = Signal(str)
    update_checked = Signal(dict)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_fonts()
        init_language()
        self.resize(600, 790)
        self.setMinimumSize(560, 710)
        self.setAcceptDrops(True)
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
        
        # Header Row mit zentriertem Titel und Einstellungen-Button rechts oben
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        
        spacer_left = QWidget()
        spacer_left.setFixedSize(28, 28)
        header_row.addWidget(spacer_left)
        
        self.header_label = QLabel()
        self.header_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.header_label.setAlignment(Qt.AlignCenter)
        header_row.addWidget(self.header_label, stretch=1)
        
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(get_rune_icon("settings", normal_color="#AEAEB2", active_color="#F2F2F7", size=20))
        self.settings_btn.setIconSize(QSize(20, 20))
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: #48484A; border-radius: 14px; }")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self.show_settings)
        header_row.addWidget(self.settings_btn)
        
        self.main_layout.addLayout(header_row)

        self.info_label = QLabel()
        self.info_label.setStyleSheet("font-size: 14px; color: #AEAEB2;")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.info_label)
        self.main_layout.addSpacing(20)

        # Action Area
        self.action_widget = QWidget()
        self.action_layout = QVBoxLayout(self.action_widget)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        
        self.select_btn = QPushButton()
        self.select_btn.setMinimumHeight(50)
        self.select_btn.setStyleSheet(SELECT_BTN_STYLE)
        self.select_btn.clicked.connect(self.open_file)
        self.action_layout.addWidget(self.select_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate default
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(PROGRESS_BAR_STYLE)
        self.progress_bar.hide()
        self.action_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #AEAEB2;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.action_layout.addWidget(self.status_label)

        self.cancel_btn = QPushButton(tr("cancel"))
        self.cancel_btn.setMinimumHeight(32)
        self.cancel_btn.setStyleSheet(CANCEL_BTN_STYLE)
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
        self.alert_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF453A;")
        self.alert_label.setAlignment(Qt.AlignCenter)
        self.result_layout.addWidget(self.alert_label)
        
        self.timecodes_textbox = QTextEdit()
        self.timecodes_textbox.setMaximumHeight(80)
        self.timecodes_textbox.setReadOnly(True)
        self.timecodes_textbox.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2E;
                color: #F2F2F7;
                border: 1px solid #48484A;
                border-radius: 6px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                padding: 4px;
            }
        """)
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
            self.canvas.setMinimumHeight(200)
            self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
            self.ax = self.figure.subplots()
            self._setup_plot_style()
            self.adv_layout.addWidget(self.canvas)

        # Export Actions direkt unterhalb des Graphen
        self.export_actions_layout = QHBoxLayout()
        self.export_actions_layout.setContentsMargins(0, 6, 0, 0)
        self.export_actions_layout.setSpacing(10)

        self.export_pdf_btn = QPushButton()
        self.export_pdf_btn.setMinimumHeight(36)
        self.export_pdf_btn.setIconSize(QSize(16, 16))
        self.export_pdf_btn.setCursor(Qt.PointingHandCursor)
        self.export_pdf_btn.clicked.connect(self.export_pdf_report)

        self.copy_values_btn = QPushButton()
        self.copy_values_btn.setMinimumHeight(36)
        self.copy_values_btn.setIconSize(QSize(16, 16))
        self.copy_values_btn.setCursor(Qt.PointingHandCursor)
        self.copy_values_btn.clicked.connect(self.copy_values_to_clipboard)

        self.export_actions_layout.addWidget(self.export_pdf_btn, stretch=1)
        self.export_actions_layout.addWidget(self.copy_values_btn, stretch=1)
        self.adv_layout.addLayout(self.export_actions_layout)

        self.result_layout.addWidget(self.adv_widget)
        
        self.main_layout.addWidget(self.result_widget)
        self.main_layout.addStretch()

        # Bottom Bar: Entwickler-Info Button (gemäß entwickler-info Skill)
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 8, 0, 0)
        
        self.dev_info_btn = QPushButton()
        self.dev_info_btn.setIcon(get_rune_icon("info", normal_color="#AEAEB2", active_color="#F2F2F7", size=14))
        self.dev_info_btn.setIconSize(QSize(14, 14))
        self.dev_info_btn.setCursor(Qt.PointingHandCursor)
        self.dev_info_btn.setStyleSheet(DEV_INFO_BTN_STYLE)
        self.dev_info_btn.clicked.connect(self.show_info)
        bottom_layout.addWidget(self.dev_info_btn)
        bottom_layout.addStretch()

        self.main_layout.addLayout(bottom_layout)
        
        self.current_file = None
        self.current_result = None
        self.total_duration = None
        self.analyzed_streams = []
        self.selected_stream_indices = []
        self._closing = False

        self._copy_feedback_timer = QTimer(self)
        self._copy_feedback_timer.setSingleShot(True)
        self._copy_feedback_timer.timeout.connect(self._reset_copy_btn_state)

        self._pdf_feedback_timer = QTimer(self)
        self._pdf_feedback_timer.setSingleShot(True)
        self._pdf_feedback_timer.timeout.connect(self._reset_pdf_btn_state)

        self.update_texts()
        self._start_update_check()

    def _start_update_check(self):
        def _check():
            res = check_for_updates(VERSION)
            if not self._closing:
                self.signals.update_checked.emit(res)
        threading.Thread(target=_check, daemon=True).start()

    def on_update_checked(self, result):
        if self._closing:
            return
        if result and result.get("has_update"):
            self.update_banner.set_update_info(result)

    def _setup_plot_style(self):
        if MATPLOTLIB_AVAILABLE:
            setup_dark_plot_axes(self.ax, self.figure)

    def update_texts(self):
        self.setWindowTitle(tr("app_title"))
        self.header_label.setText(tr("header"))
        self.info_label.setText(tr("info_text"))
        self.select_btn.setText(tr("select_file"))
        self.cancel_btn.setText(tr("cancel"))
        self.settings_btn.setToolTip(tr("settings_title"))
        self.dev_info_btn.setText(f" {tr('dev_info_btn')}")
        self.dev_info_btn.setToolTip(tr("info_title"))
        self._reset_pdf_btn_state()
        self._reset_copy_btn_state()

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

    def dragEnterEvent(self, event):
        if not self.select_btn.isEnabled() or not event.mimeData().hasUrls():
            event.ignore()
            return
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if local_path and os.path.isfile(local_path):
                self.select_btn.setStyleSheet(SELECT_BTN_DRAG_STYLE)
                event.acceptProposedAction()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.select_btn.setStyleSheet(SELECT_BTN_STYLE)
        event.accept()

    def dropEvent(self, event):
        self.select_btn.setStyleSheet(SELECT_BTN_STYLE)
        if not self.select_btn.isEnabled() or not event.mimeData().hasUrls():
            event.ignore()
            return
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if local_path and os.path.isfile(local_path):
                event.acceptProposedAction()
                self.current_file = local_path
                self.start_analysis_flow()
                return
        event.ignore()

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
        self.total_duration = None
        self.analyzed_streams = []
        self.selected_stream_indices = []
        self.progress_bar.setRange(0, 0)
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

        self.analyzed_streams = list(streams)
        self.total_duration = extract_duration(streams)
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
        self.selected_stream_indices = list(stream_indices)
        if self.total_duration and self.total_duration > 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        else:
            self.progress_bar.setRange(0, 0)
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
        if self.total_duration and self.total_duration > 0:
            pct = min(100, max(0, int(round((t / self.total_duration) * 100))))
            self.progress_bar.setValue(pct)
            use_hours = self.total_duration >= 3600
            cur_str = format_short_time(min(t, self.total_duration), force_hours=use_hours)
            tot_str = format_short_time(self.total_duration, force_hours=use_hours)
            self.status_label.setText(
                f"<span style='font-family: \"JetBrains Mono\", monospace;'>{pct} % • {cur_str} / {tot_str}</span>"
            )
        else:
            self.status_label.setText(tr("analyzing_time", t))

    def on_analyze_done(self, result):
        if self.cancel_event.is_set() or result.get("Cancelled"):
            self.set_loading(False, tr("analysis_cancelled"))
            return

        if self.total_duration and self.total_duration > 0:
            self.progress_bar.setValue(100)
        self.set_loading(False, tr("analysis_done"))
        
        if result.get("I") is None:
            self.on_error(tr("analysis_failed"))
            return
            
        self.current_result = result
        self.result_widget.show()
        self._display_result(result)

    def closeEvent(self, event):
        self._closing = True
        self._copy_feedback_timer.stop()
        self._pdf_feedback_timer.stop()
        self.cancel_analysis()
        event.accept()

    def _display_result(self, result):
        gain = result["Gain"]
        sign = "+" if gain >= 0 else ""
        
        # Rot wenn größer als 1dB + oder - (> 1.0 oder < -1.0), Grün wenn im Bereich [-1.0, 1.0]
        if round(abs(gain), 1) > 1.0:
            gain_color = "#FF453A"  # Rot
        else:
            gain_color = "#30D158"  # Grün
            
        gain_prefix = tr("gain_adjustment", "", "").split(":")[0] + ":"
        self.gain_label.setText(
            f"<span style='color: #F2F2F7;'>{gain_prefix} </span>"
            f"<span style='color: {gain_color}; font-family: \"JetBrains Mono\", monospace;'>{sign}{gain:.1f} dB</span>"
        )
        self.gain_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        
        events = result.get("Peak_Events", [])
        if events:
            self.alert_label.show()
            if len(events) == 1:
                self.alert_label.setText(tr("warning_peak_single"))
            else:
                self.alert_label.setText(tr("warning_peak_multi", len(events)))
            
            lines = [format_peak_event_line(ev) for ev in events]
            self.timecodes_textbox.show()
            self.timecodes_textbox.setText("\n".join(lines))
            if self.height() < 790:
                self.resize(self.width(), 790)
        else:
            self.alert_label.hide()
            self.timecodes_textbox.hide()
            
        i_val = "N/A" if result["I"] is None else result["I"]
        lra_val = "N/A" if result["LRA"] is None else result["LRA"]
        tp_val = "N/A" if result["Peak"] is None else result["Peak"]
        
        i_str = f"{i_val} LUFS" if i_val != "N/A" else "N/A"
        lra_str = f"{lra_val} LU" if lra_val != "N/A" else "N/A"
        tp_str = f"{tp_val} dBTP" if tp_val != "N/A" else "N/A"
        
        self.i_label.setText(f"Integrated (I): <span style='font-family: \"JetBrains Mono\", monospace; font-weight: 600; color: #F2F2F7;'>{i_str}</span>")
        self.lra_label.setText(f"Loudness Range (LRA): <span style='font-family: \"JetBrains Mono\", monospace; font-weight: 600; color: #F2F2F7;'>{lra_str}</span>")
        self.tp_label.setText(f"True Peak (Max): <span style='font-family: \"JetBrains Mono\", monospace; font-weight: 600; color: #F2F2F7;'>{tp_str}</span>")
        filename = os.path.basename(self.current_file) if self.current_file else "N/A"
        file_prefix = tr("file_label", "").split(":")[0] + ":"
        self.file_label.setText(f"{file_prefix} <span style='font-family: \"JetBrains Mono\", monospace; color: #AEAEB2;'>{filename}</span>")

        # Update Plot
        if MATPLOTLIB_AVAILABLE:
            draw_dark_loudness_plot(self.ax, self.figure, self.canvas, result)

    def _reset_pdf_btn_state(self):
        self._pdf_feedback_timer.stop()
        self.export_pdf_btn.setText(f" {tr('export_pdf_btn')}")
        self.export_pdf_btn.setToolTip(tr("export_pdf_btn"))
        self.export_pdf_btn.setIcon(get_rune_icon("file-text", normal_color="#00FF8B", active_color="#33FFAA", size=16))
        self.export_pdf_btn.setStyleSheet(REPORT_BTN_PRIMARY_STYLE)

    def _reset_copy_btn_state(self):
        self._copy_feedback_timer.stop()
        self.copy_values_btn.setText(f" {tr('copy_values_btn')}")
        self.copy_values_btn.setToolTip(tr("copy_values_btn"))
        self.copy_values_btn.setIcon(get_rune_icon("copy", normal_color="#F2F2F7", active_color="#00FF8B", size=16))
        self.copy_values_btn.setStyleSheet(REPORT_BTN_SECONDARY_STYLE)

    def _report_context(self) -> tuple[float | None, str | None]:
        dur = self.total_duration or extract_duration(self.analyzed_streams)
        summary = format_stream_summary(self.analyzed_streams, self.selected_stream_indices)
        return dur, summary

    def copy_values_to_clipboard(self):
        if not self.current_result:
            return
        dur, summary = self._report_context()
        text = build_clipboard_report(self.current_result, self.current_file, duration_sec=dur, stream_summary=summary)
        QApplication.clipboard().setText(text)
        self.copy_values_btn.setText(f" {tr('copied_feedback')}")
        self.copy_values_btn.setIcon(get_rune_icon("check", normal_color="#30D158", active_color="#30D158", size=16))
        self.copy_values_btn.setStyleSheet(REPORT_BTN_SUCCESS_STYLE)
        self._copy_feedback_timer.start(2000)

    def export_pdf_report(self):
        if not self.current_result:
            return
        suggested = suggest_pdf_filename(self.current_file)
        output_path, _ = QFileDialog.getSaveFileName(self, tr("pdf_save_dialog"), suggested, tr("pdf_file_filter"))
        if not output_path:
            return
        if not output_path.lower().endswith(".pdf"):
            output_path += ".pdf"

        dur, summary = self._report_context()
        try:
            generate_pdf_report(output_path, self.current_result, self.current_file, duration_sec=dur, stream_summary=summary)
        except Exception as e:
            QMessageBox.critical(self, tr("error"), tr("pdf_save_error", str(e)))
            return

        self.status_label.setText(tr("pdf_saved_status", os.path.basename(output_path)))
        self.export_pdf_btn.setText(f" {tr('pdf_saved_feedback')}")
        self.export_pdf_btn.setIcon(get_rune_icon("check", normal_color="#30D158", active_color="#30D158", size=16))
        self.export_pdf_btn.setStyleSheet(REPORT_BTN_SUCCESS_STYLE)
        self._pdf_feedback_timer.start(2500)

def run_app():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("de.ggfplanet.ebur128scanner")
        except Exception:
            pass

    app = QApplication(sys.argv)
    setup_app_theme(app)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
