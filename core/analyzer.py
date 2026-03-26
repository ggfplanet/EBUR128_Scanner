import subprocess
import re
import static_ffmpeg

static_ffmpeg.add_paths()

def format_timecode(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def analyze_loudness(file_path, stream_indices, progress_callback=None):
    if not stream_indices:
        stream_indices = [0]
        
    inputs = ["-i", file_path]
    
    if len(stream_indices) > 1:
        mix_inputs = "".join([f"[0:a:{i}]" for i in stream_indices])
        filter_complex = f"{mix_inputs}amix=inputs={len(stream_indices)}[mixed];[mixed]ebur128=peak=true"
    else:
        filter_complex = f"[0:a:{stream_indices[0]}]ebur128=peak=true"

    cmd = [
        "ffmpeg",
        "-nostats",
        *inputs,
        "-filter_complex", filter_complex,
        "-f", "null",
        "-"
    ]

    process = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )

    t_exceeded_times = []
    summary_data = {
        "I": None,
        "LRA": None,
        "Peak": None,
        "Gain": None,
        "Exceeded_Timecodes": [],
        "Time_Points": [],
        "Loudness_Values": [],
        "Peak_Exceedances": [],
    }

    # Regex for per-interval output: capturing t, S (short term), and TPK (True peak)
    # Example format: [Parsed_ebur128_0 @ 0x...] t: 0.1 M: -13.1 S: -13.1 I: -13.1 LUFS | LRA: 0.0 LU | TPK: -10.0
    # Note: Temporal lines often use 'TPK:', whereas the summary at the end uses 'True peak:'
    line_re = re.compile(r"t:\s*([\d\.]+).*?S:\s*([-+\d\.]+).*?(?:True peak|TPK):\s*([-+\d\.]+)")
    i_re = re.compile(r"I:\s*([-+\d\.]+)\s*LUFS")
    lra_re = re.compile(r"LRA:\s*([-+\d\.]+)\s*LU")
    peak_re = re.compile(r"Peak:\s*([-+\d\.]+)\s*dBTP")
    
    for line in process.stderr:
        m_prog = line_re.search(line)
        if m_prog:
            t_str, s_str, peak_str = m_prog.groups()
            try:
                t_val = float(t_str)
                s_val = float(s_str)
                peak_val = float(peak_str)
                
                summary_data["Time_Points"].append(t_val)
                summary_data["Loudness_Values"].append(s_val)
                
                if peak_val > -1.0:
                    t_exceeded_times.append(t_val)
                    summary_data["Peak_Exceedances"].append((t_val, s_val))
                
                if progress_callback:
                    progress_callback(t_val)
            except ValueError:
                pass
                
        m_i = i_re.search(line)
        if m_i: summary_data["I"] = float(m_i.group(1))
        
        m_lra = lra_re.search(line)
        if m_lra: summary_data["LRA"] = float(m_lra.group(1))
        
        m_peak = peak_re.search(line)
        if m_peak: summary_data["Peak"] = float(m_peak.group(1))

    process.wait()
    
    if summary_data["I"] is not None:
        summary_data["Gain"] = round(-23.0 - summary_data["I"], 2)

    clean_t = []
    last_t = -10
    for t in t_exceeded_times:
        if t - last_t > 1.0:
            clean_t.append(format_timecode(t))
            last_t = t
            
    summary_data["Exceeded_Timecodes"] = clean_t
    return summary_data
