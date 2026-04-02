import sys
import os


import traceback

def main_with_crash_handler():
    try:
        # Initialize static_ffmpeg early
        try:
            import static_ffmpeg
            static_ffmpeg.add_paths()
        except Exception as e:
            os.environ["SCANNER_INIT_ERROR"] = str(e)

        # Create dummy streams ONLY if we are in windowed mode and they are None
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w")

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

