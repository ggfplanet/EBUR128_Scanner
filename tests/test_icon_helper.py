import unittest
import sys
from PySide6.QtWidgets import QApplication
from ui.icon_helper import get_rune_icon, get_icon_path


class TestIconHelper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_rune_icons_exist_and_render(self):
        for name in ["settings", "info", "close", "zap"]:
            path = get_icon_path(name)
            self.assertTrue(path.is_file(), f"Icon file missing: {path}")
            icon = get_rune_icon(name)
            self.assertFalse(icon.isNull(), f"Icon failed to render: {name}")
            sizes = icon.availableSizes()
            self.assertTrue(len(sizes) > 0, f"No sizes available for icon: {name}")


if __name__ == "__main__":
    unittest.main()

