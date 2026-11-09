"""
Update-Banner Komponente für PySide6 gemäß tim-update Skill.
Zeigt eine nicht-blockierende Benachrichtigung an, wenn eine neuere Version verfügbar ist,
und ermöglicht ein 1-Klick Terminal In-Place Update (macOS) bzw. Browser-Weiterleitung (Windows).
"""

import sys
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from ui.i18n import tr
from core.update_service import (
    execute_terminal_update,
    DEFAULT_DOWNLOAD_URL,
    DEFAULT_MAC_INSTALL_CMD,
)


class UpdateBanner(QWidget):
    """
    Dezentes, dismissbares Banner am oberen Rand des Hauptfensters.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.update_info = None
        self.download_url = DEFAULT_DOWNLOAD_URL
        self.mac_install_cmd = DEFAULT_MAC_INSTALL_CMD
        self.is_updating = False
        self.hide()  # Standardmäßig unsichtbar

        # Widget-Styling: Dezenter Akzent mit feinem blauen Rand
        self.setObjectName("updateBanner")
        self.setStyleSheet("""
            #updateBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #1a2a3a, stop:1 #222d38);
                border: 1px solid #2a82da;
                border-radius: 6px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 10, 8)
        layout.setSpacing(10)

        # Icon / Emoji
        icon_label = QLabel("✨")
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)

        # Textbereich (Titel + Release-Notes Vorschau)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
        text_layout.addWidget(self.title_label)

        self.notes_label = QLabel()
        self.notes_label.setStyleSheet("color: #9ab4cc; font-size: 11px;")
        self.notes_label.setWordWrap(True)
        text_layout.addWidget(self.notes_label)

        layout.addLayout(text_layout, stretch=1)

        # Ladehinweis während des In-Place Updates auf macOS
        self.updating_label = QLabel()
        self.updating_label.setStyleSheet("color: #5bc0de; font-size: 11px; font-weight: bold; padding: 0 6px;")
        self.updating_label.hide()
        layout.addWidget(self.updating_label)

        # "⚡️ Jetzt aktualisieren" Button
        self.download_btn = QPushButton()
        self.download_btn.setFixedHeight(28)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a82da;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3b93eb;
            }
        """)
        self.download_btn.clicked.connect(self._on_update_clicked)
        layout.addWidget(self.download_btn)

        # Dismiss / Schließen Button (✕)
        self.dismiss_btn = QPushButton("✕")
        self.dismiss_btn.setFixedSize(24, 24)
        self.dismiss_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8899a6;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.dismiss_btn.clicked.connect(self.hide)
        layout.addWidget(self.dismiss_btn)

    def set_update_info(self, info: dict):
        """
        Aktualisiert den Banner-Inhalt und blendet das Banner ein, falls has_update True ist.
        """
        self.update_info = info
        self.is_updating = False
        self.updating_label.hide()
        self.download_btn.show()

        if not info or not info.get("has_update"):
            self.hide()
            return

        self.download_url = info.get("download_url") or info.get("downloadUrl") or self.download_url
        self.mac_install_cmd = info.get("mac_install_cmd") or info.get("macInstallCmd") or self.mac_install_cmd
        self.update_texts()
        self.show()

    def update_texts(self):
        """
        Aktualisiert die Sprachtexte und Pflicht-Tooltips des Banners.
        """
        if not self.update_info:
            return

        latest = self.update_info.get("latest_version") or self.update_info.get("latestVersion") or ""
        current = self.update_info.get("current_version") or self.update_info.get("currentVersion") or ""
        self.title_label.setText(tr("update_available_title", latest, current))

        notes = self.update_info.get("release_notes") or self.update_info.get("releaseNotes") or ""
        first_line = notes.strip().split("\n")[0] if notes else ""
        if first_line:
            self.notes_label.setText(first_line)
            self.notes_label.setToolTip(notes.strip())  # Pflicht-Tooltip für vollständige Release Notes
            self.notes_label.show()
        else:
            self.notes_label.setToolTip("")
            self.notes_label.hide()

        self.updating_label.setText(tr("update_running"))
        self.download_btn.setText(tr("update_btn"))

        if sys.platform == "darwin":
            self.download_btn.setToolTip(tr("update_btn_tooltip_mac"))
        else:
            self.download_btn.setToolTip(tr("update_btn_tooltip_win"))

        self.dismiss_btn.setToolTip(tr("update_dismiss"))

    def _on_update_clicked(self):
        """
        Plattform-differenzierte Aktion gemäß tim-update:
        - macOS: Startet das Terminal-Update entkoppelt und zeigt Ladehinweis im Banner.
        - Windows: Öffnet die Download-URL im Standardbrowser.
        """
        if sys.platform == "darwin":
            self.is_updating = True
            self.download_btn.hide()
            self.updating_label.setText(tr("update_running"))
            self.updating_label.show()
            execute_terminal_update(self.mac_install_cmd, self.download_url)
        else:
            if self.download_url:
                QDesktopServices.openUrl(QUrl(self.download_url))
