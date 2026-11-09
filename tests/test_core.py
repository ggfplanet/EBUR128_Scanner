"""
Unit tests for core logic: analyzer and scanner.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.analyzer import parse_ebur128_summary, cluster_peak_events
from core.scanner import get_standard_selection


class TestScannerSelection(unittest.TestCase):
    def test_single_surround_selection(self):
        streams = [{"index": 0, "audio_index": 0, "channels": 6, "codec_name": "aac"}]
        self.assertEqual(get_standard_selection(streams), [0])

    def test_single_stereo_selection(self):
        streams = [{"index": 0, "audio_index": 0, "channels": 2, "codec_name": "pcm_s16le"}]
        self.assertEqual(get_standard_selection(streams), [0])

    def test_dual_mono_stream_selection(self):
        streams = [
            {"index": 0, "audio_index": 0, "channels": 1, "codec_name": "pcm_s24le"},
            {"index": 1, "audio_index": 1, "channels": 1, "codec_name": "pcm_s24le"}
        ]
        self.assertEqual(get_standard_selection(streams), [0, 1])

    def test_ambiguous_two_stereo_streams_require_user_choice(self):
        streams = [
            {"index": 0, "audio_index": 0, "channels": 2, "codec_name": "pcm_s16le"},
            {"index": 1, "audio_index": 1, "channels": 2, "codec_name": "pcm_s16le"}
        ]
        self.assertIsNone(get_standard_selection(streams))

    def test_empty_streams(self):
        self.assertIsNone(get_standard_selection([]))


class TestAnalyzerParsing(unittest.TestCase):
    def test_parse_ebur128_summary(self):
        sample_output = """
        [Parsed_ebur128_0 @ 0x12345678] Summary:
          Integrated loudness:
            I:         -23.0 LUFS
            Threshold: -33.0 LUFS
          Loudness range:
            LRA:         6.5 LU
            Threshold: -43.0 LUFS
            LRA low:   -26.0 LUFS
            LRA high:  -19.5 LUFS
          True peak:
            Peak:       -1.5 dBFS
        """
        result = parse_ebur128_summary(sample_output)
        self.assertEqual(result.get("I"), -23.0)
        self.assertEqual(result.get("LRA"), 6.5)
        self.assertEqual(result.get("Peak"), -1.5)
        self.assertAlmostEqual(result.get("Gain"), 0.0, places=2)

    def test_parse_ebur128_summary_legacy_format(self):
        sample_output = """
        [Parsed_ebur128_0 @ 0x12345678] Summary:
          Integrated loudness:
            I:         -20.5 LUFS
            Threshold: -30.5 LUFS
          Loudness range:
            LRA:         5.0 LU
            Threshold: -40.5 LUFS
          True peak:
            True peak:  -0.8 dBTP
        """
        result = parse_ebur128_summary(sample_output)
        self.assertEqual(result.get("I"), -20.5)
        self.assertEqual(result.get("LRA"), 5.0)
        self.assertEqual(result.get("Peak"), -0.8)
        self.assertAlmostEqual(result.get("Gain"), -2.5, places=2)

    def test_cluster_peak_events(self):
        raw_peaks = [
            (1.0, -0.5),
            (1.2, -0.2),
            (1.5, -0.4),
            (10.0, -0.8),
            (10.5, -0.1),
        ]
        events = cluster_peak_events(raw_peaks, max_gap=1.0)
        self.assertEqual(len(events), 2)
        
        # First cluster
        self.assertEqual(events[0]["start"], 1.0)
        self.assertEqual(events[0]["end"], 1.5)
        self.assertEqual(events[0]["max_peak"], -0.2)

        # Second cluster
        self.assertEqual(events[1]["start"], 10.0)
        self.assertEqual(events[1]["end"], 10.5)
        self.assertEqual(events[1]["max_peak"], -0.1)


if __name__ == "__main__":
    unittest.main()
