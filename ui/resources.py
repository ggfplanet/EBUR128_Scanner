import sys
import os
import subprocess
from ui.i18n import tr


def format_user_error(e: Exception) -> str:
    """Übersetzt technische Exceptions in nutzerfreundliche Fehlermeldungen."""
    msg_str = str(e).lower()
    if "4551" in msg_str or "anwendungssteuerungsrichtlinie" in msg_str or "application control" in msg_str:
        return tr("error_app_control_blocked")
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
            return os.path.abspath(candidate)
    return os.path.abspath(candidates[0]) if candidates else relative_path


_fonts_initialized = False


def init_fonts():
    """Registriert Plus Jakarta Sans und JetBrains Mono in Qt und Matplotlib."""
    global _fonts_initialized
    if _fonts_initialized:
        return
    _fonts_initialized = True
    
    pjs_path = get_resource_path("assets/fonts/PlusJakartaSans-Variable.ttf")
    jbm_path = get_resource_path("assets/fonts/JetBrainsMono-Variable.ttf")
    
    try:
        from PySide6.QtGui import QFontDatabase
        if os.path.exists(pjs_path):
            QFontDatabase.addApplicationFont(pjs_path)
        if os.path.exists(jbm_path):
            QFontDatabase.addApplicationFont(jbm_path)
    except Exception:
        pass
        
    try:
        import matplotlib.font_manager as fm
        if os.path.exists(pjs_path):
            fm.fontManager.addfont(pjs_path)
        if os.path.exists(jbm_path):
            fm.fontManager.addfont(jbm_path)
    except Exception:
        pass


SELECT_BTN_STYLE = """
    QPushButton {
        background-color: #2C2C2E;
        color: #00FF8B;
        font-size: 16px;
        font-weight: bold;
        border: 1px solid #00FF8B;
        border-radius: 8px;
    }
    QPushButton:hover {
        background-color: #3A3A3C;
        border-color: #33FFAA;
        color: #33FFAA;
    }
    QPushButton:pressed {
        background-color: #1C1C1E;
        border-color: #00CC6A;
    }
    QPushButton:disabled {
        background-color: #242426;
        border: 1px solid #3A3A3C;
        color: #636366;
    }
"""

SELECT_BTN_DRAG_STYLE = """
    QPushButton {
        background-color: #3A3A3C;
        color: #33FFAA;
        font-size: 16px;
        font-weight: bold;
        border: 2px solid #33FFAA;
        border-radius: 8px;
    }
"""

PROGRESS_BAR_STYLE = """
    QProgressBar {
        background-color: #2C2C2E;
        border: 1px solid #3A3A3C;
        border-radius: 4px;
    }
    QProgressBar::chunk {
        background-color: #00FF8B;
        border-radius: 3px;
    }
"""


def setup_app_theme(app):
    """Konfiguriert Schriften, App-Icon und das dunkle Farbschema für die QApplication."""
    from PySide6.QtGui import QPalette, QColor, QFont, QIcon

    app.setStyle("Fusion")
    init_fonts()

    app_font = QFont("Plus Jakarta Sans", 10)
    app_font.setStyleHint(QFont.SansSerif)
    app.setFont(app_font)

    icon_rel = (
        "assets/icon.ico"
        if sys.platform == "win32" and os.path.exists(get_resource_path("assets/icon.ico"))
        else "assets/EBUR128_scanner_icon-macOS-Default-1024x1024@1x.png"
    )
    icon_path = get_resource_path(icon_rel)
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        if not icon.isNull():
            app.setWindowIcon(icon)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1C1C1E"))
    palette.setColor(QPalette.WindowText, QColor("#F2F2F7"))
    palette.setColor(QPalette.Base, QColor("#1C1C1E"))
    palette.setColor(QPalette.AlternateBase, QColor("#2C2C2E"))
    palette.setColor(QPalette.ToolTipBase, QColor("#3A3A3C"))
    palette.setColor(QPalette.ToolTipText, QColor("#F2F2F7"))
    palette.setColor(QPalette.Text, QColor("#F2F2F7"))
    palette.setColor(QPalette.Button, QColor("#3A3A3C"))
    palette.setColor(QPalette.ButtonText, QColor("#F2F2F7"))
    palette.setColor(QPalette.BrightText, QColor("#FF453A"))
    palette.setColor(QPalette.Link, QColor("#00FF8B"))
    palette.setColor(QPalette.Highlight, QColor("#00FF8B"))
    palette.setColor(QPalette.HighlightedText, QColor("#1C1C1E"))
    palette.setColor(QPalette.PlaceholderText, QColor("#636366"))
    app.setPalette(palette)
