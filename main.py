import sys
import os


import traceback

def main_with_crash_handler():
    try:
        # Create dummy streams FIRST because --windowed mode on Windows has no console handles.
        # This prevents any subprocesses or print statements in external libraries from hanging the app.
        if sys.stdin is None:
            sys.stdin = open(os.devnull, "r")
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w")

        # Give our current executable directory priority in PATH so bundled ffmpeg is found implicitly
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            os.environ["PATH"] = base_dir + os.pathsep + os.environ.get("PATH", "")

        from ui.app import run_app
        run_app()

    except Exception as e:
        # Write crash log to Desktop or Temp so the user can find it
        crash_log_path = os.path.join(os.path.expanduser("~"), "Desktop", "EBUR128_Scanner_Crash_Log.txt")
        try:
            with open(crash_log_path, "w") as f:
                f.write("A critical error occurred:\n\n")
                traceback.print_exc(file=f)
        except:
            pass
        # Ensure process exits
        sys.exit(1)

if __name__ == "__main__":
    main_with_crash_handler()

