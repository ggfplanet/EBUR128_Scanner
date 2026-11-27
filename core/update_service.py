from __future__ import annotations

"""
Update-Service gemäß dem tim-update Skill.
Führt eine leichtgewichtige, asynchrone und fail-silente Versionsprüfung durch
und unterstützt das 1-Klick Terminal In-Place Update auf macOS sowie Web-Redirect auf Windows.
"""

import json
import platform
import re
import subprocess
import tempfile
import urllib.request
import urllib.error
import webbrowser
import shutil
from pathlib import Path

UPDATE_URL = "https://ggfplanet.de/ebur128scanner/version.json"
DEFAULT_DOWNLOAD_URL = "https://ggfplanet.de/ebur128scanner/"
DEFAULT_MAC_INSTALL_CMD = "curl -fsSL https://ggfplanet.de/ebur128scanner/install.sh | bash"
DEFAULT_WIN_INSTALL_CMD = "irm https://ggfplanet.de/ebur128scanner/install.ps1 | iex"
DEFAULT_LINUX_INSTALL_CMD = "curl -fsSL https://ggfplanet.de/ebur128scanner/install-linux.sh | bash"
TIMEOUT_SECONDS = 5

_TRUSTED_INSTALL_RE = re.compile(
    r"^(curl|wget)\s+[-\w\s]+https://ggfplanet\.de/[\w./-]+\s*\|\s*(bash|sh)$"
)


def is_trusted_install_cmd(cmd: str | None) -> bool:
    """
    Prüft flexibel, ob ein Installationsbefehl ausschließlich Skripte von https://ggfplanet.de/
    über curl/wget an bash/sh weitergibt (ohne Shell-Verkettung, Subshells oder Zeilenumbrüche).
    """
    if not isinstance(cmd, str):
        return False
    stripped = cmd.strip()
    if not stripped or any(tok in stripped for tok in ("\n", "\r", ";", "&&", "||", "`", "$(")):
        return False
    return bool(_TRUSTED_INSTALL_RE.fullmatch(stripped))


def sanitize_download_url(url: str | None) -> str:
    """Stellt sicher, dass nur offizielle HTTPS-URLs unter ggfplanet.de geöffnet werden."""
    if isinstance(url, str) and url.strip().startswith("https://ggfplanet.de/"):
        return url.strip()
    return DEFAULT_DOWNLOAD_URL


def is_newer_version(remote_version: str, current_version: str) -> bool:
    """
    Vergleicht zwei Versionsnummern (z. B. '1.5.0' > '1.4.0' oder '2.0' > '1.9.9').
    Gibt True zurück, wenn remote_version echt neuer ist als current_version.
    """
    def clean_parts(v: str):
        v = str(v).strip().lstrip("vV")
        base = v.split("-")[0]
        parts = []
        for p in base.split("."):
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(0)
        return parts

    r_parts = clean_parts(remote_version)
    c_parts = clean_parts(current_version)

    max_len = max(len(r_parts), len(c_parts))
    r_parts += [0] * (max_len - len(r_parts))
    c_parts += [0] * (max_len - len(c_parts))

    for r, c in zip(r_parts, c_parts):
        if r > c:
            return True
        if r < c:
            return False
    return False


def check_for_updates(current_version: str, update_url: str = UPDATE_URL, timeout: int = TIMEOUT_SECONDS) -> dict:
    """
    Prüft version.json auf Updates (Fail-Silent).
    Wirft niemals ungefangene Exceptions.
    """
    default_result = {
        "current_version": current_version,
        "latest_version": current_version,
        "has_update": False,
        "download_url": DEFAULT_DOWNLOAD_URL,
        "mac_install_cmd": DEFAULT_MAC_INSTALL_CMD,
        "win_install_cmd": DEFAULT_WIN_INSTALL_CMD,
        "linux_install_cmd": DEFAULT_LINUX_INSTALL_CMD,
        "release_notes": None,
        "published_at": None,
        # CamelCase aliases
        "currentVersion": current_version,
        "latestVersion": current_version,
        "hasUpdate": False,
        "downloadUrl": DEFAULT_DOWNLOAD_URL,
        "macInstallCmd": DEFAULT_MAC_INSTALL_CMD,
        "winInstallCmd": DEFAULT_WIN_INSTALL_CMD,
        "linuxInstallCmd": DEFAULT_LINUX_INSTALL_CMD,
        "releaseNotes": None,
        "publishedAt": None,
        "error": None,
    }

    try:
        req = urllib.request.Request(
            update_url,
            headers={
                "User-Agent": f"EBUR128Scanner/{current_version}",
                "Accept": "application/json",
                "Cache-Control": "no-cache",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status is not None and status != 200:
                default_result["error"] = f"HTTP {status}"
                return default_result

            charset = response.headers.get_content_charset() or "utf-8"
            payload = json.loads(response.read().decode(charset))

            latest_version = str(payload.get("latestVersion", current_version))
            download_url = str(payload.get("downloadUrl", DEFAULT_DOWNLOAD_URL))
            mac_install_cmd = payload.get("macInstallCmd") or DEFAULT_MAC_INSTALL_CMD
            win_install_cmd = payload.get("winInstallCmd") or DEFAULT_WIN_INSTALL_CMD
            linux_install_cmd = payload.get("linuxInstallCmd") or DEFAULT_LINUX_INSTALL_CMD
            release_notes = payload.get("releaseNotes")
            published_at = payload.get("publishedAt")

            has_update = is_newer_version(latest_version, current_version)

            return {
                "current_version": current_version,
                "latest_version": latest_version,
                "has_update": has_update,
                "download_url": download_url,
                "mac_install_cmd": mac_install_cmd,
                "win_install_cmd": win_install_cmd,
                "linux_install_cmd": linux_install_cmd,
                "release_notes": release_notes,
                "published_at": published_at,
                # CamelCase aliases for backwards-compatibility
                "currentVersion": current_version,
                "latestVersion": latest_version,
                "hasUpdate": has_update,
                "downloadUrl": download_url,
                "macInstallCmd": mac_install_cmd,
                "winInstallCmd": win_install_cmd,
                "linuxInstallCmd": linux_install_cmd,
                "releaseNotes": release_notes,
                "publishedAt": published_at,
                "error": None,
            }
    except Exception as e:
        default_result["error"] = str(e)
        return default_result


def execute_terminal_update(cmd: str | None = None, download_url: str = DEFAULT_DOWNLOAD_URL) -> bool:
    """
    Führt das Update gemäß tim-update Skill aus:
    - macOS/Linux: Validiert den Befehl auf ggfplanet.de und startet das Terminal-Update.
      Gibt False zurück, wenn der Befehl blockiert wurde oder das Terminal nicht startete.
    - Windows: Öffnet die offizielle Download-Webseite im Standardbrowser (um Datei-Locks & Defender-Blockaden zu vermeiden).
    """
    safe_url = sanitize_download_url(download_url)
    system = platform.system().lower()
    if system == "darwin":
        install_cmd = (cmd or DEFAULT_MAC_INSTALL_CMD).strip()
        if not is_trusted_install_cmd(install_cmd):
            return False
        script_path = Path(tempfile.gettempdir()) / "ebur128scanner_update.command"
        script_content = f"""#!/bin/bash
clear
echo "=================================================="
echo "  🚀 EBU R 128 Scanner In-Place Update..."
echo "=================================================="
echo ""
if {install_cmd}; then
    echo ""
    echo "=================================================="
    echo "  ✅ Update erfolgreich abgeschlossen."
    echo "  Dieses Terminal-Fenster kann jetzt geschlossen werden."
    echo "=================================================="
else
    EXIT_CODE=$?
    echo ""
    echo "=================================================="
    echo "  ❌ Update fehlgeschlagen (Fehlercode $EXIT_CODE)."
    echo "  Bitte prüfe die Fehlermeldungen oben."
    echo "=================================================="
fi
rm -f "{script_path}"
"""
        try:
            script_path.write_text(script_content, encoding="utf-8")
            script_path.chmod(0o755)
            subprocess.Popen(["/usr/bin/open", "-a", "Terminal", str(script_path)])
            return True
        except Exception:
            webbrowser.open(safe_url)
            return False
    elif system == "linux":
        install_cmd = (cmd or DEFAULT_LINUX_INSTALL_CMD).strip()
        if not is_trusted_install_cmd(install_cmd):
            return False
        terminal_candidates = ["x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal", "alacritty", "kitty", "xterm"]
        for term in terminal_candidates:
            if shutil.which(term):
                try:
                    term_cmd = f"{install_cmd}; echo ''; printf '%s' 'Druecke Enter zum Schliessen... '; read -r dummy"
                    if term in ("gnome-terminal", "xfce4-terminal"):
                        subprocess.Popen([term, "--", "bash", "-c", term_cmd])
                    else:
                        subprocess.Popen([term, "-e", "bash", "-c", term_cmd])
                    return True
                except Exception:
                    pass
        webbrowser.open(safe_url)
        return True
    else:
        # Windows / andere Systeme: Offizielle Landingpage im Browser öffnen
        webbrowser.open(safe_url)
        return True
