from __future__ import annotations
import subprocess
import json
from typing import Any


def get_audio_streams(file_path: str) -> list[dict[str, Any]]:
    """
    Ruft ffprobe auf und gibt eine Liste aller im File vorhandenen Audiostreams zurück.
    """
    # FFmpeg/ffprobe ist via main.py im PATH
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        file_path
    ]

    creation_flags = 0
    if hasattr(subprocess, 'CREATE_NO_WINDOW'):
        creation_flags = subprocess.CREATE_NO_WINDOW
    
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, creationflags=creation_flags)
    data = json.loads(output)
    
    audio_streams: list[dict[str, Any]] = []
    audio_idx = 0
    for s in data.get("streams", []):
        if s.get("codec_type") == "audio":
            s["audio_index"] = audio_idx
            audio_streams.append(s)
            audio_idx += 1
    return audio_streams


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
