from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QScrollArea, QComboBox, QMessageBox, QWidget
)
from PySide6.QtCore import Qt
from ui.i18n import tr, get_current_lang, set_current_lang, VERSION

def format_channel_label(ch):
    if ch == 1:
        return tr("channel_mono")
    elif ch == 2:
        return tr("channel_stereo")
    elif ch == 4:
        return tr("channel_4ch")
    elif ch == 6:
        return tr("channel_51")
    elif ch == 8:
        return tr("channel_71")
    elif isinstance(ch, int):
        return tr("channel_multi", ch)
    return str(ch)

class StreamSelectionDialog(QDialog):
    def __init__(self, streams, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("stream_sel_title"))
        self.setFixedSize(520, 370)
        self.selected_indices = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        
        self.info_label = QLabel(tr("stream_sel_info"))
        self.info_label.setStyleSheet("font-size: 13px; color: #AEAEB2;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setSpacing(10)
        
        # Smart pre-selection:
        # 1. If there's an explicit 2-channel Stereo track, pre-select only that one
        # 2. Otherwise, if there are multiple 1-channel mono tracks, pre-select the first two (stereo pair)
        # 3. Otherwise, pre-select the first track
        stereo_idx = next((i for i, s in enumerate(streams) if s.get("channels") == 2), None)
        mono_indices = [i for i, s in enumerate(streams) if s.get("channels") == 1]
        
        default_indices = set()
        if stereo_idx is not None:
            default_indices.add(stereo_idx)
        elif len(mono_indices) >= 2:
            default_indices.update(mono_indices[:2])
        elif streams:
            default_indices.add(0)

        self.checkboxes = []
        for i, s in enumerate(streams):
            idx = s["audio_index"]
            ch = s.get("channels", "?")
            codec = s.get("codec_name", "")
            channel_str = format_channel_label(ch)
            title = s.get("tags", {}).get("title")
            
            track_prefix = tr("track_prefix", idx + 1)
            if title:
                label_text = f"{track_prefix} ({title}): {channel_str}, {codec}"
            else:
                label_text = f"{track_prefix}: {channel_str}, {codec}"
            
            cb = QCheckBox(label_text)
            cb.setStyleSheet("font-size: 13px;")
            cb.setProperty("stream_index", idx)
            cb.setProperty("channels", ch if isinstance(ch, int) else 1)
            if i in default_indices:
                cb.setChecked(True)
            cb.toggled.connect(lambda checked, box=cb: self._on_cb_toggled(box, checked))
            self.checkboxes.append(cb)
            self.scroll_layout.addWidget(cb)
            
        self.scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self.btn = QPushButton(tr("analyze"))
        self.btn.clicked.connect(self.on_submit)
        self.btn.setMinimumHeight(40)
        self.btn.setStyleSheet("""
            QPushButton {
                background-color: #00FF8B;
                color: #1C1C1E;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #33FFAA;
            }
        """)
        layout.addWidget(self.btn)

    def _on_cb_toggled(self, changed_cb, checked):
        if not checked:
            return

        ch = changed_cb.property("channels")
        if ch != 1:
            # Mehrkanal-Spur gewählt: Alle anderen Spuren automatisch abwählen
            for cb in self.checkboxes:
                if cb is not changed_cb and cb.isChecked():
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
        else:
            # Mono-Spur gewählt: Alle Nicht-Mono-Spuren automatisch abwählen
            for cb in self.checkboxes:
                if cb.property("channels") != 1 and cb.isChecked():
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
        
    def on_submit(self):
        selected_cbs = [cb for cb in self.checkboxes if cb.isChecked()]
        if not selected_cbs:
            QMessageBox.warning(self, tr("error"), tr("select_at_least_one"))
            return

        # EBU R 128 Validierung:
        # Fall 1: Genau 1 Spur (beliebige Kanalanzahl: Mono, Stereo, 5.1 etc.)
        if len(selected_cbs) == 1:
            self.selected_indices = [selected_cbs[0].property("stream_index")]
            self.accept()
            return

        # Fall 2: Mehrere Spuren -> Nur diskrete Mono-Spuren (2 für Stereo oder 6 für 5.1)
        channels = [cb.property("channels") for cb in selected_cbs]
        all_mono = all(ch == 1 for ch in channels)

        if not all_mono or len(selected_cbs) not in (2, 6):
            QMessageBox.warning(self, tr("error"), tr("invalid_stream_combination"))
            return

        self.selected_indices = [cb.property("stream_index") for cb in selected_cbs]
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
        
        idx = 0 if get_current_lang() == "de" else 1
        self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)
        
        layout.addStretch()
        
        close_btn = QPushButton(tr("close"))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3C;
                color: #F2F2F7;
                font-weight: bold;
                border: 1px solid #48484A;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #48484A;
                border-color: #00FF8B;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def change_language(self):
        new_lang = self.lang_combo.currentData()
        set_current_lang(new_lang)
        self.setWindowTitle(tr("settings_title"))
        if self.parent_window:
            self.parent_window.update_texts()

class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("info_title"))
        self.setFixedWidth(510)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)
        
        # Header (Title & Subtitle)
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title_label = QLabel("<span style='font-size: 18px; font-weight: bold;'>EBU R 128 Scanner</span>")
        title_label.setStyleSheet("border: none; background: transparent;")
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel(tr("info_subtitle"))
        subtitle_label.setStyleSheet("color: #AEAEB2; font-size: 12px; border: none; background: transparent;")
        header_layout.addWidget(subtitle_label)
        layout.addLayout(header_layout)
        
        # Card 1: Entwickler-Info (gemäß entwickler-info Skill)
        creator_box = QWidget()
        creator_box.setObjectName("creatorCard")
        creator_box.setStyleSheet(
            "#creatorCard { background-color: #2C2C2E; border: 1px solid #48484A; border-radius: 8px; } "
            "QLabel { border: none; background: transparent; }"
        )
        c_layout = QVBoxLayout(creator_box)
        c_layout.setContentsMargins(16, 12, 16, 14)
        c_layout.setSpacing(8)
        
        c_head = QLabel(f"<b>{tr('info_title')}</b>")
        c_head.setStyleSheet("color: #F2F2F7; font-size: 13px;")
        c_layout.addWidget(c_head)
        
        c_body = QLabel(
            f"<table cellpadding='2' style='font-size: 12px; line-height: 1.5;'>"
            f"<tr><td style='color: #AEAEB2; width: 85px;'>{tr('info_version')}:</td><td><b style='color: #00FF8B;'>v{VERSION}</b></td></tr>"
            f"<tr><td style='color: #AEAEB2;'>{tr('info_developer')}:</td><td style='color: #F2F2F7; font-weight: 500;'>Tim Butenschön</td></tr>"
            f"<tr><td style='color: #AEAEB2;'>{tr('info_email')}:</td><td><a href='mailto:webseite@timbutenschoen.de' style='color: #00FF8B; text-decoration: none;'>webseite@timbutenschoen.de</a></td></tr>"
            f"<tr><td style='color: #AEAEB2;'>{tr('info_website')}:</td><td><a href='https://ggfplanet.de/ebur128scanner' style='color: #00FF8B; text-decoration: none;'>ggfplanet.de/ebur128scanner</a></td></tr>"
            f"<tr><td style='color: #AEAEB2;'>GitHub:</td><td><a href='https://github.com/ggfplanet/EBUR128_Scanner' style='color: #00FF8B; text-decoration: none;'>github.com/ggfplanet/EBUR128_Scanner</a></td></tr>"
            f"</table>"
        )
        c_body.setWordWrap(True)
        c_body.setOpenExternalLinks(True)
        c_body.setTextInteractionFlags(Qt.TextBrowserInteraction)
        c_layout.addWidget(c_body)
        layout.addWidget(creator_box)
        
        # Card 2: Open Source & FFmpeg Credits
        credits_box = QWidget()
        credits_box.setObjectName("creditsCard")
        credits_box.setStyleSheet(
            "#creditsCard { background-color: #2C2C2E; border: 1px solid #48484A; border-radius: 8px; } "
            "QLabel { border: none; background: transparent; }"
        )
        cr_layout = QVBoxLayout(credits_box)
        cr_layout.setContentsMargins(16, 12, 16, 14)
        cr_layout.setSpacing(6)
        
        cr_head = QLabel(f"<b>{tr('info_credits_heading')}</b>")
        cr_head.setStyleSheet("color: #F2F2F7; font-size: 13px;")
        cr_layout.addWidget(cr_head)
        
        cr_body = QLabel(
            f"{tr('info_app_license')}<br><br>"
            f"{tr('info_ffmpeg_desc')}<br>"
            f"{tr('info_ffmpeg_license')}<br>"
            f"{tr('info_ffmpeg_source')}: <a href='https://ffmpeg.org/download.html' style='color: #00FF8B; text-decoration: none;'>ffmpeg.org/download.html</a><br><br>"
            f"{tr('info_icons_credits')}"
        )
        cr_body.setWordWrap(True)
        cr_body.setOpenExternalLinks(True)
        cr_body.setTextInteractionFlags(Qt.TextBrowserInteraction)
        cr_body.setStyleSheet("font-size: 12px; line-height: 1.45;")
        cr_layout.addWidget(cr_body)
        layout.addWidget(credits_box)
        
        layout.addSpacing(4)
        
        # Bottom Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton(tr("close"))
        close_btn.setMinimumWidth(100)
        close_btn.setMinimumHeight(32)
        close_btn.setStyleSheet(
            "QPushButton { background-color: #3A3A3C; color: #F2F2F7; border: 1px solid #48484A; border-radius: 6px; font-weight: bold; } "
            "QPushButton:hover { background-color: #48484A; border-color: #00FF8B; }"
        )
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
