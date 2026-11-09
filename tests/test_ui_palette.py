import sys
import unittest
from PySide6.QtWidgets import QApplication
from ui.app import MainWindow


class TestUIPaletteAndGain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()

    def test_gain_color_within_one_db(self):
        # ±1.0 dB Bereich -> Grün (#30D158)
        for gain in [0.0, 0.5, -0.5, 1.0, -1.0]:
            result = {
                "Gain": gain,
                "I": -23.0 - gain,
                "LRA": 4.0,
                "Peak": -2.0,
                "Peak_Events": [],
                "Time_Points": [],
                "Loudness_Values": [],
                "Peak_Exceedances": [],
            }
            self.window._display_result(result)
            text = self.window.gain_label.text()
            self.assertIn("#30D158", text, f"Gain {gain} dB should be green (#30D158)")
            self.assertNotIn("#FF453A", text, f"Gain {gain} dB should not be red")

    def test_gain_color_greater_than_one_db(self):
        # Außerhalb des ±1.0 dB Bereichs -> Rot (#FF453A)
        for gain in [1.1, -1.1, 2.5, -3.0, 10.0, -8.4]:
            result = {
                "Gain": gain,
                "I": -23.0 - gain,
                "LRA": 4.0,
                "Peak": -0.5,
                "Peak_Events": [],
                "Time_Points": [],
                "Loudness_Values": [],
                "Peak_Exceedances": [],
            }
            self.window._display_result(result)
            text = self.window.gain_label.text()
            self.assertIn("#FF453A", text, f"Gain {gain} dB should be red (#FF453A)")
            self.assertNotIn("#30D158", text, f"Gain {gain} dB should not be green")

    def test_format_user_error_winerror_4551(self):
        from ui.app import format_user_error
        err = OSError(4551, "Eine Anwendungssteuerungsrichtlinie hat diese Datei blockiert")
        msg = format_user_error(err)
        self.assertIn("Smart App Control", msg)

    def test_fonts_registered(self):
        from PySide6.QtGui import QFontDatabase
        families = QFontDatabase.families()
        self.assertIn("Plus Jakarta Sans", families)
        self.assertIn("JetBrains Mono", families)

    def test_determinate_progress_bar(self):
        self.window.total_duration = 235.0  # 03:55
        self.window.progress_bar.setRange(0, 100)
        self.window.update_progress(83.0)   # 01:23 -> 35%
        self.assertEqual(self.window.progress_bar.value(), 35)
        self.assertIn("35 % • 01:23 / 03:55", self.window.status_label.text())

    def test_indeterminate_progress_fallback(self):
        self.window.total_duration = None
        self.window.progress_bar.setRange(0, 0)
        self.window.update_progress(12.3)
        self.assertIn("12.3s", self.window.status_label.text())

    def test_accept_drops_enabled(self):
        self.assertTrue(self.window.acceptDrops())


if __name__ == "__main__":
    unittest.main()

