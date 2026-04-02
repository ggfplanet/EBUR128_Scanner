import subprocess
import json

def get_audio_streams(file_path):
    # static_ffmpeg is already initialized in main.py
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
    
    # Try to execute ffprobe. If it's not found, this will raise FileNotFoundError
    # pointing the user to the real issue (missing ffprobe)
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, creationflags=creation_flags)
    data = json.loads(output)
    
    audio_streams = []
    # get audio streams and add explicit index
    audio_idx = 0
    for s in data.get("streams", []):
        if s.get("codec_type") == "audio":
            s["audio_index"] = audio_idx
            audio_streams.append(s)
            audio_idx += 1
    return audio_streams


def is_standard_layout(audio_streams):
    """
    Checks if the files contains exactly:
    1 Stereo Track (2 channels)
    2 Mono Tracks (1 channel)
    OR exactly 1 track in total (e.g. 1 Stereo)
    """
    if len(audio_streams) == 1:
        return True
        
    if len(audio_streams) != 3:
        return False
        
    channels = [s.get("channels", 0) for s in audio_streams]
    if channels.count(2) == 1 and channels.count(1) == 2:
        return True
    return False
