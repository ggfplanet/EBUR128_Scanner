VERSION = "1.6.0"

TRANSLATIONS = {
    "de": {
        "app_title": "EBU R 128 Scanner",
        "header": "Lautheitsanalyse EBU R 128",
        "info_text": "Wähle eine Audio- oder Videodatei aus, um die Lautheit zu messen.",
        "select_file": "Datei Auswählen",
        "reading_structure": "Dateistruktur wird gelesen...",
        "no_audio": "Keine Audiospuren gefunden oder Datei konnte nicht gelesen werden.",
        "standard_layout": "Standard-Layout erkannt. Analysiere...",
        "analyzing_tracks": "Analysiere {} Spur(en)...",
        "analyzing_time": "Analysiere Film-Zeit: {:.1f}s",
        "analysis_done": "Analyse abgeschlossen.",
        "analysis_failed": "Analyse fehlgeschlagen (FFmpeg gab keine Lautheits-Daten aus).",
        "analysis_cancelled": "Analyse abgebrochen.",
        "cancel": "Abbrechen",
        "gain_adjustment": "Anpassung: {}{} dB",
        "warning_peak_single": "Warnung: True-Peak (> -1 dBTP) überschritten (1 Ereignis)!",
        "warning_peak_multi": "Warnung: True-Peak (> -1 dBTP) überschritten ({} Ereignisse)!",
        "peak_event_range": "{} – {}  (Dauer: {:.1f}s, Max: {})",
        "peak_event_point": "{}  (Max: {})",
        "i_label": "Integrated (I): {} LUFS",
        "lra_label": "Loudness Range (LRA): {} LU",
        "tp_label": "True Peak (Max): {} dBTP",
        "file_label": "Datei: {}",
        "error": "Fehler",
        "error_ffmpeg_not_found": "FFmpeg bzw. FFprobe wurde auf dem System nicht gefunden.\nBitte stelle sicher, dass die Anwendung vollständig installiert ist.",
        "error_file_read": "Die Datei konnte nicht gelesen oder verarbeitet werden.\nMöglicherweise ist die Datei beschädigt oder das Format wird nicht unterstützt.",
        "error_app_control_blocked": "Windows Smart App Control oder eine Sicherheitsrichtlinie blockiert FFmpeg/FFprobe.\n\nLösung:\n1. Öffne die Eigenschaften der blockierten Datei (Rechtsklick auf ffmpeg.exe / ffprobe.exe -> Eigenschaften).\n2. Aktiviere ganz unten das Häkchen bei 'Zulassen' bzw. 'Entsperren'.\nAlternativ installiere die App über den empfohlenen Terminal-Befehl von der Webseite.",
        "error_general": "Ein Fehler ist aufgetreten:\n{}",
        "stream_sel_title": "Tonspurauswahl",
        "stream_sel_info": "Die Datei enthält mehrere Tonspuren.\nBitte wähle die zu messende Tonspur (oder 2 Mono-Spuren für Stereo):",
        "track_prefix": "Tonspur {}",
        "channel_mono": "Mono (1 Kanal)",
        "channel_stereo": "Stereo (2 Kanäle)",
        "channel_4ch": "4 Kanäle (Spatial Audio)",
        "channel_51": "5.1 Surround (6 Kanäle)",
        "channel_71": "7.1 Surround (8 Kanäle)",
        "channel_multi": "{} Kanäle",
        "analyze": "Analysieren",
        "select_at_least_one": "Bitte mindestens eine Tonspur auswählen!",
        "invalid_stream_combination": "Ungültige Auswahl: Mehrere Spuren können nur zusammengeführt werden, wenn es sich um diskrete Mono-Spuren handelt (2 Spuren für Stereo oder 6 für 5.1).",
        "file_dialog": "Datei auswählen",
        "media_files": "Media Files (*.*)",
        "info_title": "Entwickler-Info",
        "dev_info_btn": "Entwickler-Info",
        "info_version": "Version",
        "info_developer": "Entwickler",
        "info_email": "E-Mail",
        "info_website": "Webseite",
        "info_subtitle": "Lautheitsanalyse nach EBU R 128 & ITU-R BS.1770",
        "info_creator_heading": "Entwicklung & Projekt",
        "info_credits_heading": "Credits & Open-Source-Lizenzen",
        "info_app_license": "Der <b>EBU R 128 Scanner</b> ist freie Software unter der <a href='https://www.gnu.org/licenses/gpl-3.0.html' style='color: #00FF8B; text-decoration: none;'>GNU GPL v3.0</a>.",
        "info_icons_credits": "UI-Icons: <a href='https://runeicons.com' style='color: #00FF8B; text-decoration: none;'>Rune Icons</a> (<a href='https://www.apache.org/licenses/LICENSE-2.0' style='color: #00FF8B; text-decoration: none;'>Apache-2.0</a>)",
        "info_ffmpeg_desc": "Dieses Programm nutzt das Open-Source-Projekt <b>FFmpeg</b> für die Medien- und Lautheitsanalyse.",
        "info_ffmpeg_license": "Lizenz: <b>GNU GPL v3.0</b> (bzw. LGPL v2.1+)",
        "info_ffmpeg_source": "Quellcode",
        "project_link_text": "GitHub Projekt",
        "settings_title": "Einstellungen",
        "language": "Sprache:",
        "close": "Schließen",
        "legend_s": "Short-Term (S)",
        "legend_target": "Ziel (-23 LUFS)",
        "legend_peak": "Peak (> -1 dBTP)",
        "plot_time": "Zeit (s)",
        "plot_lufs": "LUFS",
        "update_available_title": "Update verfügbar: v{} (Aktuell: v{})",
        "update_btn": "Jetzt aktualisieren",
        "update_btn_tooltip_mac": "Öffnet die Konsole, aktualisiert die App und beendet dieses Fenster.",
        "update_btn_tooltip_win": "Öffnet die Webseite im Browser zum Herunterladen des Updates.",
        "update_running": "⏳ Update läuft... App schließt gleich automatisch.",
        "update_dismiss": "Schließen",
        "update_blocked_title": "Automatisches Update blockiert",
        "update_blocked_msg": "Der automatische Update-Befehl wurde aus Sicherheitsgründen blockiert.\n\nBitte lade die aktuelle Version direkt auf der offiziellen Webseite herunter:\n{}",
        "export_pdf_btn": "PDF-Bericht speichern",
        "copy_values_btn": "Werte kopieren",
        "copied_feedback": "Kopiert!",
        "pdf_saved_feedback": "PDF gespeichert!",
        "pdf_saved_status": "PDF-Bericht gespeichert: {}",
        "pdf_save_dialog": "PDF-Bericht speichern",
        "pdf_file_filter": "PDF-Dokument (*.pdf)",
        "pdf_save_error": "PDF-Bericht konnte nicht gespeichert werden:\n{}",
        "pdf_filename_suffix": "EBU_R128_Bericht",
        "report_title": "Lautheitsanalyse-Bericht",
        "report_subtitle": "EBU R 128 / ITU-R BS.1770",
        "report_analyzed_file": "Analysierte Datei",
        "report_duration": "Dauer",
        "report_audio_track": "Tonspur",
        "report_date": "Datum",
        "report_norm": "Standard",
        "report_status_compliant": "EBU R 128 konform",
        "report_status_action": "Anpassung erforderlich",
        "report_status_peak": "True-Peak überschritten",
        "report_kpi_gain": "Pegelanpassung",
        "report_kpi_gain_sub": "Toleranz: ±1,0 LU",
        "report_kpi_integrated": "Integrated (I)",
        "report_kpi_integrated_sub": "Zielwert: -23,0 LUFS",
        "report_kpi_lra": "Loudness Range (LRA)",
        "report_kpi_lra_sub": "Dynamikumfang",
        "report_kpi_peak": "True Peak (Max)",
        "report_kpi_peak_sub": "Grenzwert: -1,0 dBTP",
        "report_graph_heading": "Lautheitsverlauf (Short-Term Loudness)",
        "report_graph_scale": "Skala: EBU +18 (-60 bis +3 LUFS)",
        "report_graph_time_axis": "Zeit",
        "report_graph_no_data": "Keine Verlaufsdaten verfügbar.",
        "report_peaks_heading": "True-Peak-Überschreitungen (> -1,0 dBTP)",
        "report_peaks_none": "Keine True-Peak-Überschreitungen über -1,0 dBTP festgestellt.",
        "report_peaks_col_num": "#",
        "report_peaks_col_tc": "Timecode",
        "report_peaks_col_dur": "Dauer",
        "report_peaks_col_peak": "Max. True Peak",
        "report_peaks_point": "Einzelimpuls (< 0,3 s)",
        "report_page": "Seite {} / {}",
        "report_clipboard_header": "EBU R 128 Scanner – Lautheitsanalyse",
        "report_clipboard_measurements": "Messergebnisse (Ziel: -23,0 LUFS / Max. -1,0 dBTP)",
        "report_clipboard_status": "Status",
        "report_clipboard_footer": "Erstellt mit {} v{} ({})",
        "report_legend_tolerance": "Toleranz (±1 LU)",
    },
    "en": {
        "app_title": "EBU R 128 Scanner",
        "header": "Loudness Analysis EBU R 128",
        "info_text": "Select an audio or video file to measure loudness.",
        "select_file": "Select File",
        "reading_structure": "Reading file structure...",
        "no_audio": "No audio tracks found or file could not be read.",
        "standard_layout": "Standard layout detected. Analyzing...",
        "analyzing_tracks": "Analyzing {} track(s)...",
        "analyzing_time": "Analyzing movie time: {:.1f}s",
        "analysis_done": "Analysis complete.",
        "analysis_failed": "Analysis failed (FFmpeg returned no loudness data).",
        "analysis_cancelled": "Analysis cancelled.",
        "cancel": "Cancel",
        "gain_adjustment": "Adjustment: {}{} dB",
        "warning_peak_single": "Warning: True-Peak (> -1 dBTP) exceeded (1 event)!",
        "warning_peak_multi": "Warning: True-Peak (> -1 dBTP) exceeded ({} events)!",
        "peak_event_range": "{} – {}  (Duration: {:.1f}s, Max: {})",
        "peak_event_point": "{}  (Max: {})",
        "i_label": "Integrated (I): {} LUFS",
        "lra_label": "Loudness Range (LRA): {} LU",
        "tp_label": "True Peak (Max): {} dBTP",
        "file_label": "File: {}",
        "error": "Error",
        "error_ffmpeg_not_found": "FFmpeg / FFprobe was not found on your system.\nPlease make sure the application components are installed properly.",
        "error_file_read": "The file could not be read or processed.\nThe file may be corrupted or the format is unsupported.",
        "error_app_control_blocked": "Windows Smart App Control or an application policy has blocked FFmpeg/FFprobe.\n\nSolution:\n1. Open properties of the blocked file (Right-click ffmpeg.exe / ffprobe.exe -> Properties).\n2. Check 'Unblock' at the bottom of the General tab.\nAlternatively, run the recommended PowerShell install command from the website.",
        "error_general": "An error occurred:\n{}",
        "stream_sel_title": "Audio Track Selection",
        "stream_sel_info": "The file contains multiple audio tracks.\nPlease select the track to measure (or 2 mono tracks for stereo):",
        "track_prefix": "Track {}",
        "channel_mono": "Mono (1 Channel)",
        "channel_stereo": "Stereo (2 Channels)",
        "channel_4ch": "4 Channels (Spatial Audio)",
        "channel_51": "5.1 Surround (6 Channels)",
        "channel_71": "7.1 Surround (8 Channels)",
        "channel_multi": "{} Channels",
        "analyze": "Analyze",
        "select_at_least_one": "Please select at least one audio track!",
        "invalid_stream_combination": "Invalid selection: Multiple tracks can only be combined if they are discrete mono tracks (2 tracks for stereo or 6 for 5.1).",
        "file_dialog": "Select File",
        "media_files": "Media Files (*.*)",
        "info_title": "Developer Info",
        "dev_info_btn": "Developer Info",
        "info_version": "Version",
        "info_developer": "Developer",
        "info_email": "Email",
        "info_website": "Website",
        "info_subtitle": "Loudness analysis according to EBU R 128 & ITU-R BS.1770",
        "info_creator_heading": "Development & Project",
        "info_credits_heading": "Credits & Open Source Licenses",
        "info_app_license": "<b>EBU R 128 Scanner</b> is free open-source software licensed under the <a href='https://www.gnu.org/licenses/gpl-3.0.html' style='color: #00FF8B; text-decoration: none;'>GNU GPL v3.0</a>.",
        "info_icons_credits": "UI Icons: <a href='https://runeicons.com' style='color: #00FF8B; text-decoration: none;'>Rune Icons</a> (<a href='https://www.apache.org/licenses/LICENSE-2.0' style='color: #00FF8B; text-decoration: none;'>Apache-2.0</a>)",
        "info_ffmpeg_desc": "This software uses the open-source project <b>FFmpeg</b> for media and loudness analysis.",
        "info_ffmpeg_license": "License: <b>GNU GPL v3.0</b> (or LGPL v2.1+)",
        "info_ffmpeg_source": "Source code",
        "project_link_text": "GitHub Project",
        "settings_title": "Settings",
        "language": "Language:",
        "close": "Close",
        "legend_s": "Short-Term (S)",
        "legend_target": "Target (-23 LUFS)",
        "legend_peak": "Peak (> -1 dBTP)",
        "plot_time": "Time (s)",
        "plot_lufs": "LUFS",
        "update_available_title": "Update available: v{} (Current: v{})",
        "update_btn": "Update Now",
        "update_btn_tooltip_mac": "Opens Terminal, updates the app in-place, and closes this window.",
        "update_btn_tooltip_win": "Opens the website in your browser to download the update.",
        "update_running": "⏳ Updating... App will close automatically.",
        "update_dismiss": "Dismiss",
        "update_blocked_title": "Automatic Update Blocked",
        "update_blocked_msg": "The automatic update command was blocked for security reasons.\n\nPlease download the latest version directly from the official website:\n{}",
        "export_pdf_btn": "Save PDF Report",
        "copy_values_btn": "Copy Values",
        "copied_feedback": "Copied!",
        "pdf_saved_feedback": "PDF Saved!",
        "pdf_saved_status": "PDF report saved: {}",
        "pdf_save_dialog": "Save PDF Report",
        "pdf_file_filter": "PDF Document (*.pdf)",
        "pdf_save_error": "Could not save PDF report:\n{}",
        "pdf_filename_suffix": "EBU_R128_Report",
        "report_title": "Loudness Analysis Report",
        "report_subtitle": "EBU R 128 / ITU-R BS.1770",
        "report_analyzed_file": "Analyzed File",
        "report_duration": "Duration",
        "report_audio_track": "Audio Track",
        "report_date": "Date",
        "report_norm": "Standard",
        "report_status_compliant": "EBU R 128 Compliant",
        "report_status_action": "Adjustment Required",
        "report_status_peak": "True-Peak Exceeded",
        "report_kpi_gain": "Gain Adjustment",
        "report_kpi_gain_sub": "Tolerance: ±1.0 LU",
        "report_kpi_integrated": "Integrated (I)",
        "report_kpi_integrated_sub": "Target: -23.0 LUFS",
        "report_kpi_lra": "Loudness Range (LRA)",
        "report_kpi_lra_sub": "Dynamic Range",
        "report_kpi_peak": "True Peak (Max)",
        "report_kpi_peak_sub": "Limit: -1.0 dBTP",
        "report_graph_heading": "Loudness Profile (Short-Term Loudness)",
        "report_graph_scale": "Scale: EBU +18 (-60 to +3 LUFS)",
        "report_graph_time_axis": "Time",
        "report_graph_no_data": "No loudness profile data available.",
        "report_peaks_heading": "True-Peak Exceedances (> -1.0 dBTP)",
        "report_peaks_none": "No True-Peak exceedances above -1.0 dBTP detected.",
        "report_peaks_col_num": "#",
        "report_peaks_col_tc": "Timecode",
        "report_peaks_col_dur": "Duration",
        "report_peaks_col_peak": "Max. True Peak",
        "report_peaks_point": "Transient (< 0.3 s)",
        "report_page": "Page {} / {}",
        "report_clipboard_header": "EBU R 128 Scanner – Loudness Analysis",
        "report_clipboard_measurements": "Measurements (Target: -23.0 LUFS / Max. -1.0 dBTP)",
        "report_clipboard_status": "Status",
        "report_clipboard_footer": "Generated with {} v{} ({})",
        "report_legend_tolerance": "Tolerance (±1 LU)",
    }
}

SETTINGS_ORG = "ggfplanet"
SETTINGS_APP = "EBUR128Scanner"
CURRENT_LANG = "de"


def detect_system_language() -> str:
    """Ermittelt die Systemsprache (Deutsch falls 'de', sonst standardmäßig Englisch)."""
    try:
        from PySide6.QtCore import QLocale
        loc_name = QLocale.system().name().lower()
        if loc_name.startswith("de"):
            return "de"
    except Exception:
        pass

    try:
        import locale
        loc = locale.getlocale()[0]
        if loc and loc.lower().startswith("de"):
            return "de"
    except Exception:
        pass

    return "en"


def init_language() -> str:
    """Lädt die gespeicherte Sprache aus QSettings oder ermittelt sie anhand der Systemsprache."""
    global CURRENT_LANG
    try:
        from PySide6.QtCore import QSettings
        settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        saved = settings.value("language")
        if saved in TRANSLATIONS:
            CURRENT_LANG = str(saved)
            return CURRENT_LANG
    except Exception:
        pass

    CURRENT_LANG = detect_system_language()
    return CURRENT_LANG


def get_current_lang() -> str:
    return CURRENT_LANG


def set_current_lang(lang: str, persist: bool = True):
    global CURRENT_LANG
    if lang in TRANSLATIONS:
        CURRENT_LANG = lang
        if persist:
            try:
                from PySide6.QtCore import QSettings
                settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
                settings.setValue("language", lang)
            except Exception:
                pass


def tr(key: str, *args) -> str:
    text = TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["de"]).get(key, key)
    if args:
        return text.format(*args)
    return text


# Initiale Erkennung beim Modulladen
init_language()
