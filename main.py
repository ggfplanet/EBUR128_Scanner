import sys
import os

# Set writeable path for static_ffmpeg if on Windows and frozen (PyInstaller)
if getattr(sys, 'frozen', False) and os.name == 'nt':
    local_app_data = os.getenv('LOCALAPPDATA')
    if local_app_data:
        # Create a dedicated directory for our ffmpeg binaries in LocalAppData
        ffmpeg_dir = os.path.join(local_app_data, "EBUR128Scanner", "ffmpeg")
        os.makedirs(ffmpeg_dir, exist_ok=True)
        # Point static_ffmpeg to this directory
        os.environ["STATFF_HOME"] = ffmpeg_dir

# Initialize static_ffmpeg early
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception as e:
    print(f"Warning: Could not initialize static_ffmpeg: {e}")

# Create dummy streams if they are None (typical with PyInstaller --windowed)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from ui.app import run_app

if __name__ == "__main__":
    run_app()

