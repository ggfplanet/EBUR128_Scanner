"""
Unit tests for update_service according to tim-update skill.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.update_service import (
    is_newer_version,
    check_for_updates,
    DEFAULT_MAC_INSTALL_CMD,
    DEFAULT_WIN_INSTALL_CMD,
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


if __name__ == "__main__":
    unittest.main()
