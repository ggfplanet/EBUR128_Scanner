import os
import sys
import io
import shutil
import subprocess
import urllib.request
import zipfile

URL = "https://github.com/Tyrrrz/FFmpegBin/releases/download/9.0.2/ffmpeg-osx-arm64.zip"

def download_and_extract(force=False):
    if not force and os.path.exists("ffmpeg") and os.path.exists("ffprobe"):
        print("Static Apple Silicon FFmpeg binaries already exist in current directory.")
        return

    print(f"Downloading static Apple Silicon (ARM64) FFmpeg from {URL}...")
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            data = resp.read()

        with zipfile.ZipFile(io.BytesIO(data)) as zipped:
            for binary in ["ffmpeg", "ffprobe"]:
                print(f"Extracting {binary}...")
                with zipped.open(binary) as src, open(binary, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                os.chmod(binary, 0o755)
                # Remove quarantine and sign ad-hoc to satisfy macOS Gatekeeper
                try:
                    subprocess.run(["xattr", "-cr", binary], check=False)
                    subprocess.run(["codesign", "--force", "-s", "-", binary], check=False)
                except Exception:
                    pass

        print("Success! Native Apple Silicon FFmpeg binaries are ready.")
    except Exception as e:
        print(f"Failed to download FFmpeg for macOS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    force_download = "--force" in sys.argv
    download_and_extract(force=force_download)
