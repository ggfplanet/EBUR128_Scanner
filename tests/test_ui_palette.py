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
            stylesheet = self.window.gain_label.styleSheet()
            self.assertIn("#30D158", stylesheet, f"Gain {gain} dB should be green (#30D158)")
            self.assertNotIn("#FF453A", stylesheet, f"Gain {gain} dB should not be red")

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
            stylesheet = self.window.gain_label.styleSheet()
            self.assertIn("#FF453A", stylesheet, f"Gain {gain} dB should be red (#FF453A)")
            self.assertNotIn("#30D158", stylesheet, f"Gain {gain} dB should not be green")


if __name__ == "__main__":
    unittest.main()

