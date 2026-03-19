import subprocess
import json
import static_ffmpeg

static_ffmpeg.add_paths()

def get_audio_streams(file_path):
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        file_path
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
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
    except Exception as e:
        print(f"Error probing file: {e}")
        return []

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
