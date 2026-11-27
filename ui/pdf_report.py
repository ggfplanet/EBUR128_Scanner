from __future__ import annotations

"""
Seriöser, druckoptimierter A4-PDF-Berichtsgenerator für den EBU R 128 Scanner.
Rendert Berichte via PySide6 (QPdfWriter + QPainter) sowie hochauflösenden
Matplotlib-Verlaufsgraph (FigureCanvasAgg, 300 DPI) mit unseren Projektschriften
Plus Jakarta Sans und JetBrains Mono.
"""

from datetime import datetime
import os
from typing import Any

from PySide6.QtCore import QMarginsF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPainterPath,
    QPageLayout,
    QPageSize,
    QPdfWriter,
    QPen,
    QPixmap,
)

from core.analyzer import format_timecode
from core.report_formatter import (
    APP_NAME,
    APP_URL,
    APP_URL_DISPLAY,
    TRUE_PEAK_LIMIT,
    evaluate_compliance,
    format_gain_value,
    format_report_timestamp,
)
from core.scanner import format_short_time
from ui.i18n import VERSION, tr
from ui.plot_helper import render_print_chart_image
from ui.resources import get_resource_path, init_fonts

DPI = 300
PAGE_W_MM = 210.0
PAGE_H_MM = 297.0
MARGIN_X_MM = 16.0
CONTENT_W_MM = PAGE_W_MM - 2.0 * MARGIN_X_MM  # 178.0 mm

TABLE_HEADER_H_MM = 7.5
TABLE_ROW_H_MM = 6.5
PAGE1_TABLE_ROWS = 9
CONT_TABLE_ROWS = 32

# Seriöse helle Print-Palette (inspiriert von der Studio-Identität des Scanners)
C_INK = QColor("#0F172A")
C_SLATE = QColor("#475569")
C_MUTED = QColor("#64748B")
C_BRAND = QColor("#059669")
C_CARD_BG = QColor("#F8FAFC")
C_BORDER = QColor("#CBD5E1")
C_BORDER_SOFT = QColor("#E2E8F0")
C_TABLE_HEAD = QColor("#F1F5F9")
C_ZEBRA = QColor("#FAFAFC")
C_OK_FG = QColor("#15803D")
C_OK_BG = QColor("#F0FDF4")
C_OK_BORDER = QColor("#BBF7D0")
C_WARN_FG = QColor("#B91C1C")
C_WARN_BG = QColor("#FEF2F2")
C_WARN_BORDER = QColor("#FECACA")


def _mm(val_mm: float) -> float:
    return val_mm * DPI / 25.4


def _rect_mm(x: float, y: float, w: float, h: float) -> QRectF:
    return QRectF(_mm(x), _mm(y), _mm(w), _mm(h))


def _font_sans(pt: float, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    f = QFont("Plus Jakarta Sans")
    f.setStyleHint(QFont.StyleHint.SansSerif)
    f.setPointSizeF(pt)
    f.setWeight(weight)
    return f


def _font_mono(pt: float, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    f = QFont("JetBrains Mono")
    f.setStyleHint(QFont.StyleHint.Monospace)
    f.setPointSizeF(pt)
    f.setWeight(weight)
    return f


def _load_logo_pixmap() -> QPixmap:
    candidates = [
        "assets/EBUR128_scanner_icon-macOS-Default-1024x1024@1x.png",
        "icon.png",
    ]
    for rel in candidates:
        path = get_resource_path(rel)
        if os.path.exists(path):
            pm = QPixmap(path)
            if not pm.isNull():
                return pm
    return QPixmap()


def _draw_header(painter: QPainter, logo: QPixmap, timestamp_str: str) -> None:
    # Obere Akzentlinie
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(C_BRAND)
    painter.drawRect(_rect_mm(MARGIN_X_MM, 14.0, 36.0, 1.2))
    painter.setBrush(C_INK)
    painter.drawRect(_rect_mm(MARGIN_X_MM + 36.0, 14.0, CONTENT_W_MM - 36.0, 1.2))

    text_x = MARGIN_X_MM
    if not logo.isNull():
        logo_rect = _rect_mm(MARGIN_X_MM, 18.2, 12.0, 12.0)
        painter.save()
        clip = QPainterPath()
        clip.addRoundedRect(logo_rect, _mm(2.2), _mm(2.2))
        painter.setClipPath(clip)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(logo_rect.toRect(), logo)
        painter.restore()
        text_x = MARGIN_X_MM + 15.2

    painter.setFont(_font_sans(13.5, QFont.Weight.Bold))
    painter.setPen(C_INK)
    painter.drawText(
        _rect_mm(text_x, 18.0, 95.0, 7.0),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        APP_NAME,
    )

    painter.setFont(_font_sans(8.5, QFont.Weight.Normal))
    painter.setPen(C_SLATE)
    painter.drawText(
        _rect_mm(text_x, 24.8, 100.0, 5.5),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        f"{tr('report_title')}  ·  {tr('report_subtitle')}",
    )

    right_x = PAGE_W_MM - MARGIN_X_MM - 64.0
    painter.setFont(_font_mono(8.0))
    painter.setPen(C_SLATE)
    painter.drawText(
        _rect_mm(right_x, 18.4, 64.0, 5.5),
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        timestamp_str,
    )

    painter.setFont(_font_mono(7.5, QFont.Weight.Medium))
    painter.setPen(C_BRAND)
    painter.drawText(
        _rect_mm(right_x, 24.6, 64.0, 5.5),
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        f"{APP_URL_DISPLAY} · v{VERSION}",
    )

    painter.setPen(QPen(C_BORDER, _mm(0.25)))
    painter.drawLine(
        int(_mm(MARGIN_X_MM)),
        int(_mm(35.0)),
        int(_mm(PAGE_W_MM - MARGIN_X_MM)),
        int(_mm(35.0)),
    )


def _draw_footer(painter: QPainter, page_num: int, total_pages: int) -> None:
    painter.setPen(QPen(C_BORDER, _mm(0.25)))
    painter.drawLine(
        int(_mm(MARGIN_X_MM)),
        int(_mm(272.0)),
        int(_mm(PAGE_W_MM - MARGIN_X_MM)),
        int(_mm(272.0)),
    )

    painter.setFont(_font_mono(7.5))
    painter.setPen(C_MUTED)
    painter.drawText(
        _rect_mm(MARGIN_X_MM, 274.5, 130.0, 6.0),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        f"{APP_NAME} v{VERSION}  ·  {APP_URL}",
    )
    painter.drawText(
        _rect_mm(PAGE_W_MM - MARGIN_X_MM - 45.0, 274.5, 45.0, 6.0),
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        tr("report_page", page_num, total_pages),
    )


def _draw_file_banner(
    painter: QPainter,
    filename: str,
    duration_sec: float | None,
    stream_summary: str | None,
    compliance: dict[str, Any],
) -> None:
    banner_rect = _rect_mm(MARGIN_X_MM, 39.0, CONTENT_W_MM, 22.0)
    painter.setPen(QPen(C_BORDER_SOFT, _mm(0.3)))
    painter.setBrush(C_CARD_BG)
    painter.drawRoundedRect(banner_rect, _mm(2.2), _mm(2.2))

    # Status-Badge rechts
    status_text = tr(compliance["status_key"])
    badge_font = _font_sans(8.5, QFont.Weight.Bold)
    fm_badge = QFontMetricsF(badge_font, painter.device())
    badge_w_mm = min(64.0, max(38.0, fm_badge.horizontalAdvance(status_text) * 25.4 / DPI + 10.0))
    badge_x = PAGE_W_MM - MARGIN_X_MM - 4.0 - badge_w_mm
    badge_rect = _rect_mm(badge_x, 45.5, badge_w_mm, 9.0)

    is_ok = compliance["is_compliant"]
    painter.setPen(QPen(C_OK_BORDER if is_ok else C_WARN_BORDER, _mm(0.35)))
    painter.setBrush(C_OK_BG if is_ok else C_WARN_BG)
    painter.drawRoundedRect(badge_rect, _mm(4.5), _mm(4.5))
    painter.setFont(badge_font)
    painter.setPen(C_OK_FG if is_ok else C_WARN_FG)
    painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, status_text)

    left_w_mm = badge_x - (MARGIN_X_MM + 4.5) - 4.0
    painter.setFont(_font_sans(7.2, QFont.Weight.DemiBold))
    painter.setPen(C_MUTED)
    painter.drawText(
        _rect_mm(MARGIN_X_MM + 4.5, 41.2, left_w_mm, 4.2),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        tr("report_analyzed_file").upper(),
    )

    fn_font = _font_mono(10.0, QFont.Weight.Bold)
    elided_fn = QFontMetricsF(fn_font, painter.device()).elidedText(filename, Qt.TextElideMode.ElideMiddle, _mm(left_w_mm))
    painter.setFont(fn_font)
    painter.setPen(C_INK)
    painter.drawText(
        _rect_mm(MARGIN_X_MM + 4.5, 45.5, left_w_mm, 6.5),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        elided_fn,
    )

    meta_parts: list[str] = []
    if duration_sec is not None and duration_sec > 0:
        dur_str = format_short_time(duration_sec, force_hours=duration_sec >= 3600)
        meta_parts.append(f"{tr('report_duration')}: {dur_str}")
    if stream_summary:
        meta_parts.append(f"{tr('report_audio_track')}: {stream_summary}")
    meta_parts.append(f"{tr('report_norm')}: EBU R 128")

    meta_font = _font_sans(7.8)
    meta_line = QFontMetricsF(meta_font, painter.device()).elidedText(
        "   ·   ".join(meta_parts), Qt.TextElideMode.ElideRight, _mm(left_w_mm)
    )
    painter.setFont(meta_font)
    painter.setPen(C_SLATE)
    painter.drawText(
        _rect_mm(MARGIN_X_MM + 4.5, 53.0, left_w_mm, 5.2),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        meta_line,
    )


def _draw_kpi_cards(painter: QPainter, result: dict[str, Any], compliance: dict[str, Any]) -> None:
    gain = result.get("Gain")
    i_val = result.get("I")
    lra_val = result.get("LRA")
    tp_val = result.get("Peak")

    gain_color = C_OK_FG if compliance["gain_ok"] else C_WARN_FG
    peak_bad = tp_val is not None and float(tp_val) > TRUE_PEAK_LIMIT
    peak_color = C_WARN_FG if peak_bad else C_INK

    cards = [
        (
            tr("report_kpi_gain"),
            format_gain_value(gain),
            tr("report_kpi_gain_sub"),
            gain_color,
            gain_color,
        ),
        (
            tr("report_kpi_integrated"),
            f"{float(i_val):.1f} LUFS" if i_val is not None else "N/A",
            tr("report_kpi_integrated_sub"),
            C_INK,
            None,
        ),
        (
            tr("report_kpi_lra"),
            f"{float(lra_val):.1f} LU" if lra_val is not None else "N/A",
            tr("report_kpi_lra_sub"),
            C_INK,
            None,
        ),
        (
            tr("report_kpi_peak"),
            f"{float(tp_val):.1f} dBTP" if tp_val is not None else "N/A",
            tr("report_kpi_peak_sub"),
            peak_color,
            C_WARN_FG if peak_bad else None,
        ),
    ]

    card_w = 41.5
    gap = 4.0
    y = 66.0
    h = 25.0

    for idx, (title, value, subtitle, val_color, stripe_color) in enumerate(cards):
        x = MARGIN_X_MM + idx * (card_w + gap)
        rect = _rect_mm(x, y, card_w, h)
        painter.setPen(QPen(C_BORDER_SOFT, _mm(0.3)))
        painter.setBrush(C_CARD_BG)
        painter.drawRoundedRect(rect, _mm(2.0), _mm(2.0))

        if stripe_color is not None:
            painter.save()
            clip = QPainterPath()
            clip.addRoundedRect(rect, _mm(2.0), _mm(2.0))
            painter.setClipPath(clip)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(stripe_color)
            painter.drawRect(_rect_mm(x, y, 1.4, h))
            painter.restore()

        painter.setFont(_font_sans(7.4, QFont.Weight.DemiBold))
        painter.setPen(C_MUTED)
        painter.drawText(
            _rect_mm(x + 3.5, y + 3.0, card_w - 6.0, 4.5),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            title,
        )

        val_font = _font_mono(12.5, QFont.Weight.Bold)
        elided_val = QFontMetricsF(val_font, painter.device()).elidedText(value, Qt.TextElideMode.ElideRight, _mm(card_w - 6.0))
        painter.setFont(val_font)
        painter.setPen(val_color)
        painter.drawText(
            _rect_mm(x + 3.5, y + 8.8, card_w - 6.0, 8.2),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            elided_val,
        )

        painter.setFont(_font_sans(7.0))
        painter.setPen(C_SLATE)
        painter.drawText(
            _rect_mm(x + 3.5, y + 17.8, card_w - 6.0, 4.5),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            subtitle,
        )


def _draw_graph_section(painter: QPainter, result: dict[str, Any]) -> None:
    painter.setFont(_font_sans(10.5, QFont.Weight.Bold))
    painter.setPen(C_INK)
    painter.drawText(
        _rect_mm(MARGIN_X_MM, 97.0, 110.0, 6.0),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        tr("report_graph_heading"),
    )

    painter.setFont(_font_mono(7.4))
    painter.setPen(C_MUTED)
    painter.drawText(
        _rect_mm(PAGE_W_MM - MARGIN_X_MM - 68.0, 97.0, 68.0, 6.0),
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        tr("report_graph_scale"),
    )

    box_rect = _rect_mm(MARGIN_X_MM, 105.0, CONTENT_W_MM, 76.0)
    painter.setPen(QPen(C_BORDER_SOFT, _mm(0.3)))
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(box_rect, _mm(2.0), _mm(2.0))

    chart_img = render_print_chart_image(result, CONTENT_W_MM - 2.0, 74.0, dpi=DPI)
    if chart_img is not None:
        painter.save()
        clip = QPainterPath()
        clip.addRoundedRect(box_rect, _mm(2.0), _mm(2.0))
        painter.setClipPath(clip)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawImage(_rect_mm(MARGIN_X_MM + 1.0, 106.0, CONTENT_W_MM - 2.0, 74.0), chart_img)
        painter.restore()
    else:
        painter.setFont(_font_sans(9.0))
        painter.setPen(C_MUTED)
        painter.drawText(box_rect, Qt.AlignmentFlag.AlignCenter, tr("report_graph_no_data"))


def _draw_peaks_heading(painter: QPainter, y: float, event_count: int) -> None:
    painter.setFont(_font_sans(10.5, QFont.Weight.Bold))
    painter.setPen(C_INK)
    painter.drawText(
        _rect_mm(MARGIN_X_MM, y, 130.0, 6.5),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        tr("report_peaks_heading"),
    )
    count_label = f"{event_count}"
    pill_rect = _rect_mm(PAGE_W_MM - MARGIN_X_MM - 14.0, y + 0.5, 14.0, 5.5)
    is_zero = event_count == 0
    painter.setPen(QPen(C_OK_BORDER if is_zero else C_WARN_BORDER, _mm(0.3)))
    painter.setBrush(C_OK_BG if is_zero else C_WARN_BG)
    painter.drawRoundedRect(pill_rect, _mm(2.7), _mm(2.7))
    painter.setFont(_font_mono(7.8, QFont.Weight.Bold))
    painter.setPen(C_OK_FG if is_zero else C_WARN_FG)
    painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, count_label)


def _draw_peak_table_chunk(
    painter: QPainter,
    y_start: float,
    events: list[dict[str, Any]],
    start_index: int,
) -> None:
    col_x = [MARGIN_X_MM, MARGIN_X_MM + 14.0, MARGIN_X_MM + 72.0, MARGIN_X_MM + 132.0]
    col_w = [14.0, 58.0, 60.0, CONTENT_W_MM - 132.0]
    col_align = [
        Qt.AlignmentFlag.AlignLeft,
        Qt.AlignmentFlag.AlignLeft,
        Qt.AlignmentFlag.AlignLeft,
        Qt.AlignmentFlag.AlignRight,
    ]
    headers = [
        tr("report_peaks_col_num"),
        tr("report_peaks_col_tc"),
        tr("report_peaks_col_dur"),
        tr("report_peaks_col_peak"),
    ]

    # Tabellenkopf
    head_rect = _rect_mm(MARGIN_X_MM, y_start, CONTENT_W_MM, TABLE_HEADER_H_MM)
    painter.setPen(QPen(C_BORDER_SOFT, _mm(0.25)))
    painter.setBrush(C_TABLE_HEAD)
    painter.drawRect(head_rect)

    painter.setFont(_font_sans(7.8, QFont.Weight.Bold))
    painter.setPen(C_SLATE)
    for cx, cw, align, title in zip(col_x, col_w, col_align, headers):
        pad_l = 3.0 if align == Qt.AlignmentFlag.AlignLeft else 0.0
        pad_r = 3.0 if align == Qt.AlignmentFlag.AlignRight else 0.0
        painter.drawText(
            _rect_mm(cx + pad_l, y_start, cw - pad_l - pad_r, TABLE_HEADER_H_MM),
            align | Qt.AlignmentFlag.AlignVCenter,
            title,
        )

    # Zeilen
    y_row = y_start + TABLE_HEADER_H_MM
    for offset, ev in enumerate(events):
        row_num = start_index + offset + 1
        row_rect = _rect_mm(MARGIN_X_MM, y_row, CONTENT_W_MM, TABLE_ROW_H_MM)
        painter.setPen(QPen(C_BORDER_SOFT, _mm(0.2)))
        painter.setBrush(C_ZEBRA if offset % 2 == 1 else QColor("#FFFFFF"))
        painter.drawRect(row_rect)

        dur = float(ev.get("duration", 0.0))
        start_tc = format_timecode(ev["start"])
        if dur >= 0.3:
            tc_str = f"{start_tc} – {format_timecode(ev['end'])}"
            dur_str = f"{dur:.1f} s"
        else:
            tc_str = start_tc
            dur_str = tr("report_peaks_point")

        max_peak = float(ev["max_peak"])
        sign_p = "+" if max_peak >= 0 else ""
        peak_str = f"{sign_p}{max_peak:.1f} dBTP"

        cells = [
            (str(row_num), C_MUTED, QFont.Weight.Normal),
            (tc_str, C_INK, QFont.Weight.Normal),
            (dur_str, C_SLATE, QFont.Weight.Normal),
            (peak_str, C_WARN_FG, QFont.Weight.Bold),
        ]

        for cx, cw, align, (val, color, weight) in zip(col_x, col_w, col_align, cells):
            pad_l = 3.0 if align == Qt.AlignmentFlag.AlignLeft else 0.0
            pad_r = 3.0 if align == Qt.AlignmentFlag.AlignRight else 0.0
            painter.setFont(_font_mono(8.0, weight))
            painter.setPen(color)
            painter.drawText(
                _rect_mm(cx + pad_l, y_row, cw - pad_l - pad_r, TABLE_ROW_H_MM),
                align | Qt.AlignmentFlag.AlignVCenter,
                val,
            )

        y_row += TABLE_ROW_H_MM


def _paginate_events(events: list[dict[str, Any]]) -> list[tuple[int, list[dict[str, Any]]]]:
    if not events:
        return []
    chunks: list[tuple[int, list[dict[str, Any]]]] = []
    first_chunk = events[:PAGE1_TABLE_ROWS]
    chunks.append((0, first_chunk))
    idx = PAGE1_TABLE_ROWS
    while idx < len(events):
        chunks.append((idx, events[idx : idx + CONT_TABLE_ROWS]))
        idx += CONT_TABLE_ROWS
    return chunks


def generate_pdf_report(
    output_path: str,
    result: dict[str, Any],
    file_path: str | None,
    duration_sec: float | None = None,
    stream_summary: str | None = None,
    timestamp: datetime | None = None,
) -> str:
    """
    Erzeugt einen druckfertigen A4-PDF-Bericht mit Kopfzeile (inkl. Logo),
    KPI-Übersicht, 300-DPI-Lautheitsverlauf, True-Peak-Tabelle und Fußzeile.
    """
    init_fonts()

    filename = os.path.basename(file_path) if file_path else "N/A"
    ts_str = format_report_timestamp(timestamp)
    compliance = evaluate_compliance(result)
    events: list[dict[str, Any]] = list(result.get("Peak_Events") or [])
    chunks = _paginate_events(events)
    total_pages = max(1, len(chunks))

    writer = QPdfWriter(output_path)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
    writer.setResolution(DPI)
    writer.setTitle(f"{APP_NAME} – {filename}")
    writer.setCreator(f"{APP_NAME} v{VERSION} ({APP_URL})")

    painter = QPainter()
    if not painter.begin(writer):
        raise OSError(f"Could not open PDF destination: {output_path}")

    try:
        logo = _load_logo_pixmap()

        # Seite 1
        _draw_header(painter, logo, ts_str)
        _draw_file_banner(painter, filename, duration_sec, stream_summary, compliance)
        _draw_kpi_cards(painter, result, compliance)
        _draw_graph_section(painter, result)
        _draw_peaks_heading(painter, 188.0, len(events))

        if not events:
            ok_rect = _rect_mm(MARGIN_X_MM, 197.0, CONTENT_W_MM, 12.0)
            painter.setPen(QPen(C_OK_BORDER, _mm(0.3)))
            painter.setBrush(C_OK_BG)
            painter.drawRoundedRect(ok_rect, _mm(2.0), _mm(2.0))
            painter.setFont(_font_sans(8.5, QFont.Weight.Medium))
            painter.setPen(C_OK_FG)
            painter.drawText(
                _rect_mm(MARGIN_X_MM + 4.0, 197.0, CONTENT_W_MM - 8.0, 12.0),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                tr("report_peaks_none"),
            )
        else:
            start_idx, first_events = chunks[0]
            _draw_peak_table_chunk(painter, 197.0, first_events, start_idx)

        _draw_footer(painter, 1, total_pages)

        # Folgeseiten bei vielen Peak-Ereignissen
        for page_offset, (start_idx, page_events) in enumerate(chunks[1:], start=2):
            if not writer.newPage():
                raise RuntimeError("Failed to create continuation PDF page")
            _draw_header(painter, logo, ts_str)
            _draw_peaks_heading(painter, 40.0, len(events))
            _draw_peak_table_chunk(painter, 48.0, page_events, start_idx)
            _draw_footer(painter, page_offset, total_pages)
    finally:
        painter.end()

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise OSError(f"PDF file was not written properly: {output_path}")

    return output_path
