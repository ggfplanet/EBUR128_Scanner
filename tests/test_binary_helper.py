import os
import sys
import unittest

from core.binary_helper import get_binary_path, unblock_file, unblock_bundled_binaries


class TestBinaryHelper(unittest.TestCase):
    def test_get_binary_path_returns_string(self):
        ffprobe_path = get_binary_path("ffprobe")
        self.assertIsInstance(ffprobe_path, str)
        self.assertTrue(len(ffprobe_path) > 0)

        ffmpeg_path = get_binary_path("ffmpeg")
        self.assertIsInstance(ffmpeg_path, str)
        self.assertTrue(len(ffmpeg_path) > 0)

    def test_unblock_file_safe_call(self):
        # Sollte auch bei nicht existierenden Pfaden oder Nicht-Windows sicher durchlaufen
        unblock_file("non_existent_file.xyz")
        unblock_file("")

    def test_unblock_bundled_binaries_safe_call(self):
        unblock_bundled_binaries()


if __name__ == "__main__":
    unittest.main()

