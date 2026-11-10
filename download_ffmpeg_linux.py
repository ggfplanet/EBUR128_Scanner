import os
import sys
import io
import shutil
import platform
import tarfile
import urllib.request

URLS = {
    "x64": "https://github.com/FFmpeg-Builds/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
    "arm64": "https://github.com/FFmpeg-Builds/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz",
}


def get_target_arch() -> str:
    for arg in sys.argv[1:]:
        if arg.startswith("--arch="):
            val = arg.split("=", 1)[1].lower()
            if val in ("x64", "x86_64", "amd64"):
                return "x64"
            if val in ("arm64", "aarch64"):
                return "arm64"
    machine = platform.machine().lower()
    if machine in ("aarch64", "arm64"):
        return "arm64"
    return "x64"


def download_and_extract(force: bool = False, target_arch: str | None = None):
    arch = target_arch or get_target_arch()
    url = URLS.get(arch, URLS["x64"])

    if not force and os.path.exists("ffmpeg") and os.path.exists("ffprobe"):
        print(f"Static Linux ({arch}) FFmpeg binaries already exist in current directory.")
        return

    print(f"Downloading static Linux ({arch}) FFmpeg from {url}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            data = resp.read()

        with tarfile.open(fileobj=io.BytesIO(data), mode="r:xz") as tar:
            found_ffmpeg = False
            found_ffprobe = False
            for member in tar.getmembers():
                base_name = os.path.basename(member.name)
                if base_name in ("ffmpeg", "ffprobe") and member.isfile():
                    print(f"Extracting {base_name}...")
                    extracted_f = tar.extractfile(member)
                    if extracted_f:
                        with open(base_name, "wb") as dst:
                            shutil.copyfileobj(extracted_f, dst)
                        os.chmod(base_name, 0o755)
                        if base_name == "ffmpeg":
                            found_ffmpeg = True
                        elif base_name == "ffprobe":
                            found_ffprobe = True

            if not (found_ffmpeg and found_ffprobe):
                raise RuntimeError(f"Could not find both ffmpeg and ffprobe inside archive from {url}")

        print(f"Success! Static Linux ({arch}) FFmpeg binaries are ready.")
    except Exception as e:
        print(f"Failed to download FFmpeg for Linux ({arch}): {e}")
        sys.exit(1)


if __name__ == "__main__":
    force_download = "--force" in sys.argv
    download_and_extract(force=force_download)

