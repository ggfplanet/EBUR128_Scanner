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
