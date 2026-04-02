import urllib.request
import zipfile
import io
import shutil
import sys

URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

def download_and_extract():
    print(f"Downloading static FFmpeg from {URL}...")
    try:
        req = urllib.request.urlopen(URL)
        zipped = zipfile.ZipFile(io.BytesIO(req.read()))
        for info in zipped.infolist():
            if info.filename.endswith("ffmpeg.exe"):
                print("Extracting ffmpeg.exe...")
                with zipped.open(info) as src, open("ffmpeg.exe", "wb") as dst:
                    shutil.copyfileobj(src, dst)
            elif info.filename.endswith("ffprobe.exe"):
                print("Extracting ffprobe.exe...")
                with zipped.open(info) as src, open("ffprobe.exe", "wb") as dst:
                    shutil.copyfileobj(src, dst)
        print("Success! Static binaries are ready.")
    except Exception as e:
        print(f"Failed to download FFmpeg: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_and_extract()
