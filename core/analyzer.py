from __future__ import annotations
import subprocess
import re
import threading
from typing import TypedDict, Callable, Any, Iterable
from core.binary_helper import get_binary_path


class PeakEvent(TypedDict):
    start: float
    end: float
    duration: float
    max_peak: float


class LoudnessResult(TypedDict, total=False):
    I: float | None
    LRA: float | None
    Peak: float | None
    Gain: float | None
    Exceeded_Timecodes: list[str]
    Peak_Events: list[PeakEvent]
    Time_Points: list[float]
    Loudness_Values: list[float]
    Peak_Exceedances: list[tuple[float, float]]
    Cancelled: bool


def format_timecode(seconds: float | int) -> str:
    """Formatiert Sekunden in einen Timecode-String hh:mm:ss."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def cluster_peak_events(exceedances: list[tuple[float, float]], max_gap: float = 0.3) -> list[PeakEvent]:
    """
    Fasst einzelne 100-ms-True-Peak-Überschreitungen zu zusammenhängenden Ereignissen zusammen.
    exceedances ist eine Liste von (t_val, peak_val).
    """
    if not exceedances:
        return []

    events: list[PeakEvent] = []
    current_start, current_max_peak = exceedances[0]
    current_end = current_start

    for t, peak in exceedances[1:]:
        if t - current_end <= max_gap:
            current_end = t
            if peak > current_max_peak:
                current_max_peak = peak
        else:
            events.append({
                "start": current_start,
                "end": current_end,
                "duration": round(current_end - current_start, 2),
                "max_peak": current_max_peak,
            })
            current_start = t
            current_end = t
            current_max_peak = peak

    events.append({
        "start": current_start,
        "end": current_end,
        "duration": round(current_end - current_start, 2),
        "max_peak": current_max_peak,
    })

    return events


def parse_ebur128_summary(lines: Iterable[str] | str) -> dict[str, float | None]:
    """
    Parst den finalen 'Summary:'-Block aus der FFmpeg-ebur128-Ausgabe.
    Gibt ein Dict mit I, LRA, Peak und Gain zurück.
    """
    i_re = re.compile(r"I:\s*([-+\d\.]+)\s*LUFS")
    lra_re = re.compile(r"LRA:\s*([-+\d\.]+)\s*LU")
    peak_re = re.compile(r"(?:True\s+peak|Peak):\s*([-+\d\.]+)\s*(?:dBTP|dBFS)", re.IGNORECASE)

    in_summary = False
    data: dict[str, float | None] = {"I": None, "LRA": None, "Peak": None, "Gain": None}

    line_iter = lines.splitlines() if isinstance(lines, str) else lines

    for line in line_iter:
        if "Summary:" in line:
            in_summary = True
        if in_summary:
            m_i = i_re.search(line)
            if m_i:
                data["I"] = float(m_i.group(1))
            m_lra = lra_re.search(line)
            if m_lra:
                data["LRA"] = float(m_lra.group(1))
            m_peak = peak_re.search(line)
            if m_peak:
                data["Peak"] = float(m_peak.group(1))

    if data["I"] is not None:
        data["Gain"] = round(-23.0 - data["I"], 2)

    return data


def analyze_loudness(
    file_path: str,
    stream_indices: list[int] | None = None,
    progress_callback: Callable[[float], None] | None = None,
    cancel_event: threading.Event | None = None,
    on_process_started: Callable[[subprocess.Popen[str]], None] | None = None,
) -> LoudnessResult:
    """
    Führt die Lautheitsmessung nach EBU R 128 / ITU-R BS.1770 über FFmpeg durch.
    Unterstützt asynchronen Abbruch über cancel_event oder on_process_started.
    """
    if not stream_indices:
        stream_indices = [0]
        
    inputs = ["-i", file_path]
    
    if len(stream_indices) > 1:
        # Sicherheitsnetz: Jede Mono-Spur wird auf 48 kHz resampled und explizit als mono formatiert,
        # um FFmpeg-Abbrüche wegen abweichender Samplerates oder fehlender Layouts zu verhindern.
        resampled_parts = "".join([f"[0:a:{idx}]aresample=48000,aformat=channel_layouts=mono[a{i}];" for i, idx in enumerate(stream_indices)])
        merge_inputs = "".join([f"[a{i}]" for i in range(len(stream_indices))])
        filter_complex = f"{resampled_parts}{merge_inputs}amerge=inputs={len(stream_indices)}[mixed];[mixed]ebur128=peak=true"
    else:
        filter_complex = f"[0:a:{stream_indices[0]}]ebur128=peak=true"

    ffmpeg_bin = get_binary_path("ffmpeg")
    cmd = [
        ffmpeg_bin,
        "-nostats",
        *inputs,
        "-filter_complex", filter_complex,
        "-f", "null",
        "-"
    ]

    creation_flags = 0
    if hasattr(subprocess, 'CREATE_NO_WINDOW'):
        creation_flags = subprocess.CREATE_NO_WINDOW

    process: subprocess.Popen[str] = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1,
        creationflags=creation_flags
    )

    if on_process_started:
        on_process_started(process)

    raw_peaks: list[tuple[float, float]] = []
    summary_lines: list[str] = []
    summary_data: LoudnessResult = {
        "I": None,
        "LRA": None,
        "Peak": None,
        "Gain": None,
        "Exceeded_Timecodes": [],
        "Peak_Events": [],
        "Time_Points": [],
        "Loudness_Values": [],
        "Peak_Exceedances": [],
        "Cancelled": False,
    }

    # Regex für Zeitausgabe: t, S (short term), TPK (True peak)
    line_re = re.compile(r"t:\s*([\d\.]+).*?S:\s*([-+\d\.]+).*?(?:True peak|TPK):\s*([-+\d\.]+)")
    
    in_summary = False

    if process.stderr:
        for line in process.stderr:
            if cancel_event and cancel_event.is_set():
                process.terminate()
                try:
                    process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    process.kill()
                summary_data["Cancelled"] = True
                return summary_data

            # Erkennung des finalen Summary-Blocks von FFmpeg
            if "Summary:" in line:
                in_summary = True

            if in_summary:
                summary_lines.append(line)
            else:
                m_prog = line_re.search(line)
                if m_prog:
                    t_str, s_str, peak_str = m_prog.groups()
                    try:
                        t_val = float(t_str)
                        s_val = float(s_str)
                        peak_val = float(peak_str)
                        
                        summary_data["Time_Points"].append(t_val)
                        summary_data["Loudness_Values"].append(s_val)
                        
                        if peak_val > -1.0:
                            raw_peaks.append((t_val, peak_val))
                            summary_data["Peak_Exceedances"].append((t_val, s_val))
                        
                        if progress_callback:
                            progress_callback(t_val)
                    except ValueError:
                        pass

    process.wait()
    
    # Wurde der Prozess von außen während des Wartens terminiert?
    if cancel_event and cancel_event.is_set():
        summary_data["Cancelled"] = True
        return summary_data

    # Parst die gesammelten Summary-Zeilen
    parsed = parse_ebur128_summary(summary_lines)
    summary_data["I"] = parsed["I"]
    summary_data["LRA"] = parsed["LRA"]
    summary_data["Peak"] = parsed["Peak"]
    summary_data["Gain"] = parsed["Gain"]

    # Fehlerbehandlung: Wenn FFmpeg mit Fehler abbrach oder kein Summary lieferte
    if process.returncode != 0 or not in_summary or summary_data["I"] is None:
        summary_data["I"] = None
        summary_data["LRA"] = None
        summary_data["Peak"] = None
        summary_data["Gain"] = None
        return summary_data

    # Clustere zusammenhängende True-Peak-Überschreitungen zu Events
    events = cluster_peak_events(raw_peaks)
    summary_data["Peak_Events"] = events
    summary_data["Exceeded_Timecodes"] = [format_timecode(e["start"]) for e in events]
    return summary_data

