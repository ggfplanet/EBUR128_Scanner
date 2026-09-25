"""
Update-Service gemäß dem tim-update Skill.
Führt eine leichtgewichtige, asynchrone und fail-silente Versionsprüfung durch.
"""

import json
import urllib.request
import urllib.error

UPDATE_URL = "https://ggfplanet.de/ebur128scanner/version.json"
DEFAULT_DOWNLOAD_URL = "https://ggfplanet.de/ebur128scanner"
TIMEOUT_SECONDS = 5


def is_newer_version(remote_version: str, current_version: str) -> bool:
    """
    Vergleicht zwei Versionsnummern (z. B. '1.4.1' > '1.4.0' oder '2.0' > '1.9.9').
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
        "release_notes": None,
        "published_at": None,
        # CamelCase aliases
        "currentVersion": current_version,
        "latestVersion": current_version,
        "hasUpdate": False,
        "downloadUrl": DEFAULT_DOWNLOAD_URL,
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
            release_notes = payload.get("releaseNotes")
            published_at = payload.get("publishedAt")

            has_update = is_newer_version(latest_version, current_version)

            return {
                "current_version": current_version,
                "latest_version": latest_version,
                "has_update": has_update,
                "download_url": download_url,
                "release_notes": release_notes,
                "published_at": published_at,
                # CamelCase aliases for backwards-compatibility
                "currentVersion": current_version,
                "latestVersion": latest_version,
                "hasUpdate": has_update,
                "downloadUrl": download_url,
                "releaseNotes": release_notes,
                "publishedAt": published_at,
                "error": None,
            }
    except Exception as e:
        default_result["error"] = str(e)
        return default_result
