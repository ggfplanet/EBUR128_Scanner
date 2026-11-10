"""
Helper zum Auffinden und Entsperren mitgelieferter Binärdateien (FFmpeg / FFprobe).
Behebt Windows Smart App Control / Zone.Identifier Blockaden (WinError 4551).
"""

from __future__ import annotations
import os
import sys
import shutil


def unblock_file(path: str) -> None:
    """
    Entfernt auf Windows NTFS den Zone.Identifier Alternate Data Stream (Mark of the Web).
    Verhindert WinError 4551 (ERROR_APP_CONTROL_BLOCKED).
    """
    if sys.platform != "win32" or not path:
        return
    try:
        import ctypes
        ctypes.windll.kernel32.DeleteFileW(f"{path}:Zone.Identifier")
    except Exception:
        pass
    try:
        zone_stream = f"{path}:Zone.Identifier"
        if os.path.exists(zone_stream):
            os.remove(zone_stream)
    except Exception:
        pass


def unblock_bundled_binaries() -> None:
    """
    Entfernt Mark of the Web (Zone.Identifier) von allen mitgelieferten Binärdateien und DLLs.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        delete_file = ctypes.windll.kernel32.DeleteFileW
        
        candidates: list[str] = []
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            candidates.append(exe_dir)
            if hasattr(sys, "_MEIPASS"):
                candidates.append(sys._MEIPASS)
        else:
            candidates.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        for base in candidates:
            if not os.path.isdir(base):
                continue
            for root, _, files in os.walk(base):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in (".exe", ".dll"):
                        full_path = os.path.join(root, f)
                        delete_file(f"{full_path}:Zone.Identifier")
    except Exception:
        pass


def get_binary_path(name: str) -> str:
    """
    Ermittelt den absoluten Pfad zu einer Binärdatei (z. B. 'ffmpeg' oder 'ffprobe').
    Sucht priorisiert im Bundle (_MEIPASS, exe_dir, _internal, Frameworks).
    Entsperrt gefundene Binärdateien auf Windows automatisch.
    """
    binary_name = f"{name}.exe" if sys.platform == "win32" and not name.lower().endswith(".exe") else name
    
    candidates: list[str] = []
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.append(os.path.join(sys._MEIPASS, binary_name))
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, binary_name))
        candidates.append(os.path.join(exe_dir, "_internal", binary_name))
        candidates.append(os.path.normpath(os.path.join(exe_dir, "..", "Frameworks", binary_name)))
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.append(os.path.join(project_root, binary_name))
        
    for path in candidates:
        if os.path.isfile(path):
            unblock_file(path)
            if sys.platform != "win32" and not os.access(path, os.X_OK):
                try:
                    os.chmod(path, 0o755)
                except Exception:
                    pass
            return path
            
    # Fallback: Im System-PATH suchen
    system_path = shutil.which(binary_name) or shutil.which(name)
    if system_path:
        unblock_file(system_path)
        if sys.platform != "win32" and not os.access(system_path, os.X_OK):
            try:
                os.chmod(system_path, 0o755)
            except Exception:
                pass
        return system_path
        
    return binary_name

