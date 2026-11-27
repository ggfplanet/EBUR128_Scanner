from __future__ import annotations

"""
Gemeinsame Matplotlib-Plot-Funktionen für die dunkle Live-UI und den
druckoptimierten hellen PDF-Bericht (300 DPI).
Verwendet konsequent Plus Jakarta Sans und JetBrains Mono.
"""

import importlib.util
from typing import Any

from PySide6.QtGui import QImage

from core.scanner import format_short_time
from ui.i18n import tr


def setup_dark_plot_axes(ax, figure) -> None:
    """Konfiguriert das dunkle Studio-Design für den Live-Plot im Hauptfenster."""
    ax.set_facecolor("#282828")
    ax.tick_params(colors="#AEAEB2", labelsize=8)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily("JetBrains Mono")
    for side in ("bottom", "top", "left", "right"):
        ax.spines[side].set_color("#48484A")
    ax.set_xlabel(tr("plot_time"), color="#AEAEB2", fontsize=9, fontfamily="Plus Jakarta Sans")
    ax.set_ylabel(tr("plot_lufs"), color="#AEAEB2", fontsize=9, fontfamily="Plus Jakarta Sans")
    ax.set_ylim(-60, 3)
    ax.grid(True, alpha=0.2, color="#AEAEB2")
    figure.tight_layout()


def draw_dark_loudness_plot(ax, figure, canvas, result: dict[str, Any]) -> None:
    """Zeichnet den gemessenen Short-Term-Lautheitsverlauf im dunklen Live-UI."""
    ax.clear()
    setup_dark_plot_axes(ax, figure)

    times = result.get("Time_Points", [])
    loudness = result.get("Loudness_Values", [])
    peaks = result.get("Peak_Exceedances", [])

    if times and loudness:
        ax.plot(times, loudness, color="#2a82da", linewidth=1.5, label=tr("legend_s"))
        if peaks:
            px = [p[0] for p in peaks]
            py = [p[1] for p in peaks]
            ax.scatter(px, py, color="#ff5555", s=20, zorder=5, label=tr("legend_peak"))

        ax.axhline(y=-23, color="#44aa44", linestyle="--", alpha=0.6, label=tr("legend_target"))
        ax.set_ylim(-60, 3)

        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontfamily("JetBrains Mono")

        ax.legend(
            loc="lower right",
            fontsize=8,
            facecolor="#282828",
            edgecolor="#48484A",
            labelcolor="#F2F2F7",
            prop={"family": "Plus Jakarta Sans", "size": 8},
        )
        figure.tight_layout()
        canvas.draw()


def render_print_chart_image(
    result: dict[str, Any],
    width_mm: float,
    height_mm: float,
    dpi: int = 300,
) -> QImage | None:
    """Rendert den Lautheitsverlauf als 300-DPI-Druckgrafik (ohne pyplot)."""
    if importlib.util.find_spec("matplotlib") is None:
        return None
    times = result.get("Time_Points") or []
    loudness = result.get("Loudness_Values") or []
    peaks = result.get("Peak_Exceedances") or []
    if not times or not loudness:
        return None

    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.ticker import FuncFormatter

    fig = Figure(figsize=(width_mm / 25.4, height_mm / 25.4), dpi=dpi, facecolor="#FFFFFF")
    canvas = FigureCanvasAgg(fig)
    ax = fig.subplots()
    ax.set_facecolor("#FAFBFC")

    ax.axhspan(-24.0, -22.0, color="#22C55E", alpha=0.10, zorder=1, label=tr("report_legend_tolerance"))
    ax.axhline(y=-23.0, color="#16A34A", linestyle="--", linewidth=1.0, alpha=0.85, zorder=2, label=tr("legend_target"))
    ax.plot(times, loudness, color="#2563EB", linewidth=1.15, zorder=3, label=tr("legend_s"))
    ax.fill_between(times, loudness, -60.0, color="#2563EB", alpha=0.06, zorder=2)

    if peaks:
        px = [p[0] for p in peaks]
        py = [p[1] for p in peaks]
        ax.scatter(px, py, color="#DC2626", edgecolors="#FFFFFF", linewidths=0.5, s=22, zorder=5, label=tr("legend_peak"))

    ax.set_ylim(-60, 3)
    max_t = max(times)
    if len(times) > 1 and max_t > min(times):
        ax.set_xlim(min(times), max_t)

    if max_t >= 60.0:
        force_h = max_t >= 3600.0
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _pos: format_short_time(max(0.0, x), force_hours=force_h)))
        ax.set_xlabel(tr("report_graph_time_axis"), color="#334155", fontsize=8, fontfamily="Plus Jakarta Sans")
    else:
        ax.set_xlabel(tr("plot_time"), color="#334155", fontsize=8, fontfamily="Plus Jakarta Sans")

    ax.set_ylabel(tr("plot_lufs"), color="#334155", fontsize=8, fontfamily="Plus Jakarta Sans")
    ax.tick_params(colors="#475569", labelsize=7)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily("JetBrains Mono")

    for side in ("bottom", "top", "left", "right"):
        ax.spines[side].set_color("#CBD5E1")
        ax.spines[side].set_linewidth(0.75)

    ax.grid(True, color="#CBD5E1", alpha=0.5, linewidth=0.5, linestyle=":")
    ax.legend(
        loc="lower right",
        ncol=2,
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#CBD5E1",
        framealpha=0.94,
        labelcolor="#0F172A",
        prop={"family": "Plus Jakarta Sans", "size": 7},
    )

    fig.tight_layout(pad=0.55)
    canvas.draw()
    buf = canvas.buffer_rgba()
    w_px, h_px = canvas.get_width_height()
    img = QImage(bytes(buf), w_px, h_px, w_px * 4, QImage.Format.Format_RGBA8888).copy()
    fig.clear()
    return img
