from __future__ import annotations
import subprocess
import json
from typing import Any
from core.binary_helper import get_binary_path


def get_audio_streams(file_path: str) -> list[dict[str, Any]]:
    """
    Ruft ffprobe auf und gibt eine Liste aller im File vorhandenen Audiostreams zurück.
    Speichert außerdem die Gesamtdauer (in Sekunden) als 'duration_sec' im Stream-Dict, falls verfügbar.
    """
    ffprobe_bin = get_binary_path("ffprobe")
    cmd = [
        ffprobe_bin,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]

    creation_flags = 0
    if hasattr(subprocess, 'CREATE_NO_WINDOW'):
        creation_flags = subprocess.CREATE_NO_WINDOW
    
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, creationflags=creation_flags)
    data = json.loads(output)

    fmt_dur: float | None = None
    raw_fmt_dur = data.get("format", {}).get("duration")
    if raw_fmt_dur is not None:
        try:
            val = float(raw_fmt_dur)
            if val > 0:
                fmt_dur = val
        except (ValueError, TypeError):
            pass
    
    audio_streams: list[dict[str, Any]] = []
    audio_idx = 0
    for s in data.get("streams", []):
        if s.get("codec_type") == "audio":
            s["audio_index"] = audio_idx
            if "duration_sec" not in s:
                stream_dur = None
                if s.get("duration") is not None:
                    try:
                        v = float(s["duration"])
                        if v > 0:
                            stream_dur = v
                    except (ValueError, TypeError):
                        pass
                if stream_dur is not None or fmt_dur is not None:
                    s["duration_sec"] = stream_dur if stream_dur is not None else fmt_dur
            audio_streams.append(s)
            audio_idx += 1
    return audio_streams


def extract_duration(audio_streams: list[dict[str, Any]]) -> float | None:
    """
    Extrahiert die Gesamtlänge in Sekunden aus den ffprobe-Audiostreams, falls bekannt.
    """
    for s in audio_streams:
        for key in ("duration_sec", "duration"):
            val = s.get(key)
            if val is not None:
                try:
                    dur = float(val)
                    if dur > 0:
                        return dur
                except (ValueError, TypeError):
                    pass
    return None


def format_short_time(seconds: float, force_hours: bool = False) -> str:
    """
    Formatiert Sekunden als MM:SS (oder HH:MM:SS bei >= 1 Stunde bzw. force_hours=True).
    Beispiel: 83.2 -> '01:23', 235.0 -> '03:55'.
    """
    total_sec = max(0, int(round(seconds)))
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hours > 0 or force_hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def get_standard_selection(audio_streams: list[dict[str, Any]]) -> list[int] | None:
    """
    Gibt die Liste der Stream-Indizes zurück, wenn das Layout eindeutig ist,
    oder None, falls eine manuelle Nutzerauswahl erforderlich ist.
    """
    if not audio_streams:
        return None
    # Einzelne Audiospur: immer Standard (Mono, Stereo, 5.1 etc.)
    if len(audio_streams) == 1:
        return [audio_streams[0]["audio_index"]]
    # Genau 2 Spuren, beide 1-Kanal Mono: diskretes Stereopaar (L + R)
    if len(audio_streams) == 2:
        channels = [s.get("channels", 0) for s in audio_streams]
        if channels == [1, 1]:
            return [audio_streams[0]["audio_index"], audio_streams[1]["audio_index"]]
    return None
