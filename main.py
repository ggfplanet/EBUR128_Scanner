import sys
import os

# Create dummy streams if they are None (typical with PyInstaller --windowed)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from ui.app import run_app

if __name__ == "__main__":
    run_app()
