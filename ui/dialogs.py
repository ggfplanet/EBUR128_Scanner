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
        self.info_label.setStyleSheet("font-size: 13px; color: #e0e0e0;")
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
        self.btn.setStyleSheet("font-size: 14px; font-weight: bold;")
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
        title_label = QLabel(
            f"<span style='font-size: 18px; font-weight: bold;'>EBU R 128 Scanner</span> "
            f"<span style='font-size: 13px; color: #2a82da; font-weight: bold;'>v{VERSION}</span>"
        )
        title_label.setStyleSheet("border: none; background: transparent;")
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel(tr("info_subtitle"))
        subtitle_label.setStyleSheet("color: #9e9e9e; font-size: 12px; border: none; background: transparent;")
        header_layout.addWidget(subtitle_label)
        layout.addLayout(header_layout)
        
        # Card 1: Creator & Project
        creator_box = QWidget()
        creator_box.setObjectName("creatorCard")
        creator_box.setStyleSheet(
            "#creatorCard { background-color: #2b2b2b; border: 1px solid #3c3c3c; border-radius: 8px; } "
            "QLabel { border: none; background: transparent; }"
        )
        c_layout = QVBoxLayout(creator_box)
        c_layout.setContentsMargins(16, 12, 16, 14)
        c_layout.setSpacing(6)
        
        c_head = QLabel(f"<b>{tr('info_creator_heading')}</b>")
        c_head.setStyleSheet("color: #ffffff; font-size: 13px;")
        c_layout.addWidget(c_head)
        
        c_body = QLabel(
            "Tim Butenschön<br>"
            "<a href='https://ggfplanet.de/ebur128scanner' style='color: #2a82da; text-decoration: none;'>ggfplanet.de/ebur128scanner</a> &nbsp;•&nbsp; "
            f"<a href='https://github.com/ggfplanet/EBUR128_Scanner' style='color: #2a82da; text-decoration: none;'>{tr('project_link_text')}</a><br>"
            "<a href='mailto:webseite@timbutenschoen.de' style='color: #888888; text-decoration: none;'>webseite@timbutenschoen.de</a>"
        )
        c_body.setWordWrap(True)
        c_body.setOpenExternalLinks(True)
        c_body.setTextInteractionFlags(Qt.TextBrowserInteraction)
        c_body.setStyleSheet("font-size: 12px; line-height: 1.45;")
        c_layout.addWidget(c_body)
        layout.addWidget(creator_box)
        
        # Card 2: Open Source & FFmpeg Credits
        credits_box = QWidget()
        credits_box.setObjectName("creditsCard")
        credits_box.setStyleSheet(
            "#creditsCard { background-color: #2b2b2b; border: 1px solid #3c3c3c; border-radius: 8px; } "
            "QLabel { border: none; background: transparent; }"
        )
        cr_layout = QVBoxLayout(credits_box)
        cr_layout.setContentsMargins(16, 12, 16, 14)
        cr_layout.setSpacing(6)
        
        cr_head = QLabel(f"<b>{tr('info_credits_heading')}</b>")
        cr_head.setStyleSheet("color: #ffffff; font-size: 13px;")
        cr_layout.addWidget(cr_head)
        
        cr_body = QLabel(
            f"{tr('info_ffmpeg_desc')}<br>"
            f"{tr('info_ffmpeg_license')}<br>"
            f"{tr('info_ffmpeg_source')}: <a href='https://ffmpeg.org/download.html' style='color: #2a82da; text-decoration: none;'>ffmpeg.org/download.html</a>"
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
            "QPushButton { background-color: #383838; border: 1px solid #4d4d4d; border-radius: 6px; font-weight: bold; } "
            "QPushButton:hover { background-color: #444444; border-color: #2a82da; }"
        )
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
