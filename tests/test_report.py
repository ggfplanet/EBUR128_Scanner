"""
Unit tests for clipboard text report, PDF report generation, and UI export controls.
"""

from datetime import datetime
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication

from core.report_formatter import (
    APP_NAME,
    APP_URL,
    build_clipboard_report,
    evaluate_compliance,
    format_stream_summary,
    suggest_pdf_filename,
)
from ui.app import MainWindow
from ui.i18n import get_current_lang, set_current_lang
from ui.pdf_report import generate_pdf_report


def _sample_result(gain=-1.5, peak=-0.4, num_peaks=2):
    times = [i * 0.5 for i in range(40)]
    loudness = [-23.0 + ((i % 7) - 3) * 1.4 for i in range(40)]
    events = [
        {"start": 2.0 + i * 3.0, "end": 2.6 + i * 3.0, "duration": 0.6, "max_peak": peak}
        for i in range(num_peaks)
    ]
    exceedances = [(ev["start"], -20.0) for ev in events]
    return {
        "I": -23.0 - gain,
        "LRA": 5.4,
        "Peak": peak,
        "Gain": gain,
        "Peak_Events": events,
        "Time_Points": times,
        "Loudness_Values": loudness,
        "Peak_Exceedances": exceedances,
    }


class TestReportFormatter(unittest.TestCase):
    def setUp(self):
        self.orig_lang = get_current_lang()

    def tearDown(self):
        set_current_lang(self.orig_lang, persist=False)

    def test_evaluate_compliance_cases(self):
        c1 = evaluate_compliance({"Gain": 0.5, "Peak": -1.2, "Peak_Events": []})
        self.assertTrue(c1["is_compliant"])
        self.assertEqual(c1["status_key"], "report_status_compliant")

        c2 = evaluate_compliance({"Gain": -1.5, "Peak": -2.0, "Peak_Events": []})
        self.assertFalse(c2["is_compliant"])
        self.assertEqual(c2["status_key"], "report_status_action")

        c3 = evaluate_compliance({"Gain": 0.2, "Peak": -0.3, "Peak_Events": [{"start": 1.0, "end": 1.0, "duration": 0.0, "max_peak": -0.3}]})
        self.assertFalse(c3["is_compliant"])
        self.assertEqual(c3["status_key"], "report_status_peak")

    def test_format_stream_summary(self):
        set_current_lang("de", persist=False)
        streams = [{"audio_index": 0, "channels": 2, "codec_name": "pcm_s24le", "sample_rate": "48000"}]
        self.assertEqual(format_stream_summary(streams, [0]), "Stereo (2 Kanäle), pcm_s24le, 48 kHz")

        dual_mono = [
            {"audio_index": 0, "channels": 1, "codec_name": "pcm_s24le", "sample_rate": "48000"},
            {"audio_index": 1, "channels": 1, "codec_name": "pcm_s24le", "sample_rate": "48000"},
        ]
        self.assertEqual(format_stream_summary(dual_mono, [0, 1]), "2× Mono → Stereo, pcm_s24le, 48 kHz")
        self.assertIsNone(format_stream_summary([], []))

    def test_build_clipboard_report_de_and_en(self):
        res = _sample_result(gain=-1.5, peak=-0.4, num_peaks=2)
        dt = datetime(2026, 11, 27, 13, 15)

        set_current_lang("de", persist=False)
        txt_de = build_clipboard_report(res, "/tmp/demo_mix.mov", duration_sec=125.0, stream_summary="Stereo (2 Kanäle)", timestamp=dt)
        self.assertIn("demo_mix.mov", txt_de)
        self.assertIn("-1.5 dB", txt_de)
        self.assertIn("-21.5 LUFS", txt_de)
        self.assertIn("5.4 LU", txt_de)
        self.assertIn("-0.4 dBTP", txt_de)
        self.assertIn("00:00:02", txt_de)
        self.assertIn(APP_NAME, txt_de)
        self.assertIn(APP_URL, txt_de)

        set_current_lang("en", persist=False)
        txt_en = build_clipboard_report(_sample_result(gain=0.0, peak=-2.0, num_peaks=0), "/tmp/clean.wav", timestamp=dt)
        self.assertIn("clean.wav", txt_en)
        self.assertIn("EBU R 128 Compliant", txt_en)
        self.assertIn("No True-Peak exceedances", txt_en)
        self.assertIn(APP_URL, txt_en)

    def test_suggest_pdf_filename(self):
        set_current_lang("de", persist=False)
        self.assertTrue(suggest_pdf_filename("/tmp/film_final.mov").endswith("film_final_EBU_R128_Bericht.pdf"))
        set_current_lang("en", persist=False)
        self.assertTrue(suggest_pdf_filename("/tmp/film_final.mov").endswith("film_final_EBU_R128_Report.pdf"))
        self.assertTrue(suggest_pdf_filename(None).endswith("EBU_R128_Report.pdf"))


class TestPdfReportAndUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.orig_lang = get_current_lang()
        set_current_lang("de", persist=False)
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        set_current_lang(self.orig_lang, persist=False)

    def test_generate_single_page_pdf_compliant(self):
        res = _sample_result(gain=0.2, peak=-1.8, num_peaks=0)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = os.path.join(tmpdir, "compliant.pdf")
            returned = generate_pdf_report(
                out_pdf,
                res,
                "/media/Studio/final_master_mix.mov",
                duration_sec=185.0,
                stream_summary="Stereo (2 Kanäle), pcm_s24le, 48 kHz",
            )
            self.assertEqual(returned, out_pdf)
            with open(out_pdf, "rb") as f:
                raw = f.read()
            self.assertTrue(raw.startswith(b"%PDF-"))
            self.assertGreater(len(raw), 5000)

    def test_generate_multipage_pdf_and_empty_plot(self):
        res = _sample_result(gain=-2.4, peak=-0.1, num_peaks=35)
        res["Time_Points"] = []
        res["Loudness_Values"] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = os.path.join(tmpdir, "multipage.pdf")
            generate_pdf_report(out_pdf, res, "/media/clip.wav", duration_sec=600.0)
            with open(out_pdf, "rb") as f:
                raw = f.read()
            self.assertTrue(raw.startswith(b"%PDF-"))
            page_count = raw.count(b"/Type /Page\n") + raw.count(b"/Type /Page ") + raw.count(b"/Type /Page\r")
            self.assertGreaterEqual(page_count, 2)

    def test_ui_buttons_and_copy_to_clipboard(self):
        res = _sample_result(gain=0.4, peak=-1.5, num_peaks=0)
        self.window.current_file = "/tmp/broadcast_master.mxf"
        self.window.total_duration = 90.0
        self.window.current_result = res
        self.window.result_widget.show()
        self.window._display_result(res)

        self.assertFalse(self.window.export_pdf_btn.isHidden())
        self.assertFalse(self.window.copy_values_btn.isHidden())

        self.window.copy_values_to_clipboard()
        clip_text = QApplication.clipboard().text()
        self.assertIn("broadcast_master.mxf", clip_text)
        self.assertIn("+0.4 dB", clip_text)
        self.assertIn(APP_URL, clip_text)


if __name__ == "__main__":
    unittest.main()
