"""
Hilfsmodul zum Laden und Rendern von Vektor-Icons (Rune Icons, Apache-2.0).
Unterstützt Retina/HiDPI Skalierung und automatische Farbwechsel für Hover/Active-Zustände.
"""

from pathlib import Path
import sys
from PySide6.QtCore import QByteArray, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer


def get_icon_path(name: str) -> Path:
    """Ermittelt den Pfad zur SVG-Icon-Datei sowohl im Quellcode als auch im PyInstaller-Bundle."""
    filename = name if name.endswith(".svg") else f"{name}.svg"
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS) / "assets" / "icons"
    else:
        base_dir = Path(__file__).resolve().parent.parent / "assets" / "icons"
    return base_dir / filename


def get_rune_icon(
    name: str,
    normal_color: str = "#AEAEB2",
    active_color: str = "#F2F2F7",
    size: int = 24,
) -> QIcon:
    """
    Erstellt ein QIcon aus einer lokalen Rune-Icons SVG-Datei.
    Setzt 'normal_color' für den Ruhezustand und 'active_color' für Hover/Fokus.
    """
    path = get_icon_path(name)
    if not path.is_file():
        return QIcon()

    try:
        with open(path, "r", encoding="utf-8") as f:
            svg_template = f.read()
    except Exception:
        return QIcon()

    icon = QIcon()
    scale = 2  # 2x für gestochen scharfe HiDPI / Retina-Darstellung
    px_size = size * scale

    for color, mode in [(normal_color, QIcon.Normal), (active_color, QIcon.Active)]:
        colored_svg = svg_template.replace('stroke="currentColor"', f'stroke="{color}"')
        renderer = QSvgRenderer(QByteArray(colored_svg.encode("utf-8")))
        
        pixmap = QPixmap(px_size, px_size)
        pixmap.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        pixmap.setDevicePixelRatio(scale)
        icon.addPixmap(pixmap, mode)

    return icon

