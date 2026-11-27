from __future__ import annotations

"""
Formatierungs- und Auswertungslogik für den EBU-R-128-Berichtsexport (Zwischenablage & PDF).
Enthält ausschließlich reine Python-Logik ohne Qt-Abhängigkeit.
"""

from datetime import datetime
import os
from typing import Any

from core.analyzer import format_timecode
from core.scanner import format_short_time
from ui.i18n import VERSION, get_current_lang, tr

APP_NAME = "EBU R 128 Scanner"
APP_URL = "https://ggfplanet.de/ebur128scanner"
APP_URL_DISPLAY = "ggfplanet.de/ebur128scanner"
TARGET_LUFS = -23.0
TOLERANCE_LU = 1.0
TRUE_PEAK_LIMIT = -1.0


def evaluate_compliance(result: dict[str, Any]) -> dict[str, Any]:
    """
    Bewertet die EBU-R-128-Konformität anhand von Pegelanpassung (±1,0 LU)
    und True-Peak-Grenzwert (≤ -1,0 dBTP).
    """
    gain = result.get("Gain")
    gain_ok = gain is not None and round(abs(float(gain)), 1) <= TOLERANCE_LU

    peak = result.get("Peak")
    peak_events = result.get("Peak_Events") or []
    peak_ok = (peak is None or float(peak) <= TRUE_PEAK_LIMIT) and len(peak_events) == 0

    is_compliant = gain_ok and peak_ok
    if is_compliant:
        status_key = "report_status_compliant"
    elif not gain_ok:
        status_key = "report_status_action"
    else:
        status_key = "report_status_peak"

    return {
        "gain_ok": gain_ok,
        "peak_ok": peak_ok,
        "is_compliant": is_compliant,
        "status_key": status_key,
    }


def _channel_label(channels: Any) -> str:
    if channels == 1:
        return tr("channel_mono")
    if channels == 2:
        return tr("channel_stereo")
    if channels == 4:
        return tr("channel_4ch")
    if channels == 6:
        return tr("channel_51")
    if channels == 8:
        return tr("channel_71")
    if isinstance(channels, int):
        return tr("channel_multi", channels)
    return str(channels)


def _format_sample_rate(stream: dict[str, Any]) -> str | None:
    raw = stream.get("sample_rate")
    if raw is None:
        return None
    try:
        hz = int(float(raw))
        if hz <= 0:
            return None
        khz = hz / 1000.0
        if khz.is_integer():
            return f"{int(khz)} kHz"
        return f"{khz:.1f} kHz"
    except (ValueError, TypeError):
        return None


def format_stream_summary(
    streams: list[dict[str, Any]] | None,
    selected_indices: list[int] | None,
) -> str | None:
    """
    Formatiert die analysierte(n) Tonspur(en) kompakt und lokalisiert.
    Gibt None zurück, wenn keine Stream-Metadaten vorhanden sind.
    """
    if not streams:
        return None

    indices = list(selected_indices) if selected_indices else [streams[0].get("audio_index", 0)]
    by_idx = {s.get("audio_index", i): s for i, s in enumerate(streams)}
    chosen = [by_idx[idx] for idx in indices if idx in by_idx]
    if not chosen:
        chosen = [streams[0]]

    if len(chosen) > 1 and all(s.get("channels") == 1 for s in chosen):
        count = len(chosen)
        layout_target = "Stereo" if count == 2 else ("5.1" if count == 6 else f"{count}ch")
        first = chosen[0]
        parts = [f"{count}× Mono → {layout_target}"]
        codec = first.get("codec_name")
        if codec:
            parts.append(str(codec))
        sr = _format_sample_rate(first)
        if sr:
            parts.append(sr)
        return ", ".join(parts)

    s = chosen[0]
    parts = []
    ch = s.get("channels")
    if ch is not None:
        parts.append(_channel_label(ch))
    codec = s.get("codec_name")
    if codec:
        parts.append(str(codec))
    sr = _format_sample_rate(s)
    if sr:
        parts.append(sr)
    return ", ".join(parts) if parts else None


def format_report_timestamp(dt: datetime | None = None) -> str:
    """Formatiert Zeitstempel sprachabhängig für Deutschland bzw. Englisch."""
    now = dt or datetime.now()
    if get_current_lang() == "de":
        return now.strftime("%d.%m.%Y, %H:%M")
    return now.strftime("%Y-%m-%d %H:%M")


def suggest_pdf_filename(file_path: str | None) -> str:
    """Schlägt einen sinnvollen Standard-Dateinamen für den PDF-Bericht vor."""
    suffix = tr("pdf_filename_suffix")
    if file_path:
        directory = os.path.dirname(os.path.abspath(file_path))
        stem, _ = os.path.splitext(os.path.basename(file_path))
        safe_stem = stem.strip() or "EBUR128"
        return os.path.join(directory, f"{safe_stem}_{suffix}.pdf")
    home = os.path.expanduser("~")
    return os.path.join(home, f"{suffix}.pdf")


def format_gain_value(gain: float | None) -> str:
    if gain is None:
        return "N/A"
    sign = "+" if float(gain) >= 0 else ""
    return f"{sign}{float(gain):.1f} dB"


def format_peak_event_line(ev: dict[str, Any]) -> str:
    """Formatiert ein einzelnes True-Peak-Ereignis als Klartextzeile."""
    start_tc = format_timecode(ev["start"])
    max_peak = float(ev["max_peak"])
    sign_p = "+" if max_peak >= 0 else ""
    peak_str = f"{sign_p}{max_peak:.1f} dBTP"
    dur = float(ev.get("duration", 0.0))
    if dur >= 0.3:
        end_tc = format_timecode(ev["end"])
        return tr("peak_event_range", start_tc, end_tc, dur, peak_str)
    return tr("peak_event_point", start_tc, peak_str)


def build_clipboard_report(
    result: dict[str, Any],
    file_path: str | None,
    duration_sec: float | None = None,
    stream_summary: str | None = None,
    timestamp: datetime | None = None,
) -> str:
    """
    Erzeugt einen strukturierten, graphfreien Klartextbericht der Messwerte
    für die Zwischenablage.
    """
    header = tr("report_clipboard_header")
    filename = os.path.basename(file_path) if file_path else "N/A"
    compliance = evaluate_compliance(result)

    i_val = result.get("I")
    lra_val = result.get("LRA")
    tp_val = result.get("Peak")
    gain_val = result.get("Gain")

    i_str = f"{float(i_val):.1f} LUFS" if i_val is not None else "N/A"
    lra_str = f"{float(lra_val):.1f} LU" if lra_val is not None else "N/A"
    tp_str = f"{float(tp_val):.1f} dBTP" if tp_val is not None else "N/A"
    gain_str = format_gain_value(gain_val)

    lines = [
        header,
        "=" * len(header),
        f"{tr('report_analyzed_file')}: {filename}",
    ]

    if duration_sec is not None and duration_sec > 0:
        lines.append(f"{tr('report_duration')}: {format_short_time(duration_sec, force_hours=duration_sec >= 3600)}")
    if stream_summary:
        lines.append(f"{tr('report_audio_track')}: {stream_summary}")
    lines.append(f"{tr('report_date')}: {format_report_timestamp(timestamp)}")
    lines.append("")
    lines.append(tr("report_clipboard_measurements"))
    lines.append("-" * len(tr("report_clipboard_measurements")))
    lines.append(f"{tr('report_kpi_gain')}: {gain_str}")
    lines.append(f"{tr('report_kpi_integrated')}: {i_str}")
    lines.append(f"{tr('report_kpi_lra')}: {lra_str}")
    lines.append(f"{tr('report_kpi_peak')}: {tp_str}")
    lines.append(f"{tr('report_clipboard_status')}: {tr(compliance['status_key'])}")
    lines.append("")
    lines.append(tr("report_peaks_heading"))
    lines.append("-" * len(tr("report_peaks_heading")))

    events = result.get("Peak_Events") or []
    if not events:
        lines.append(tr("report_peaks_none"))
    else:
        for idx, ev in enumerate(events, start=1):
            lines.append(f"  {idx}. {format_peak_event_line(ev)}")

    lines.append("")
    lines.append(tr("report_clipboard_footer", APP_NAME, VERSION, APP_URL))
    return "\n".join(lines)
