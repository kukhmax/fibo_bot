import unittest

from core.data import Candle
from core.data import validate_candle_sequence


class TestDataQuality(unittest.TestCase):
    def test_valid_sequence(self) -> None:
        candles = [
            Candle("BTC", "1m", 0, 59_999, 100, 101, 99, 100.5, 10),
            Candle("BTC", "1m", 60_000, 119_999, 100.5, 102, 100, 101.2, 8),
        ]
        report = validate_candle_sequence("BTC", "1m", candles)
        self.assertTrue(report.is_valid)
        self.assertEqual(report.issues, ())

    def test_gap_and_invalid_values(self) -> None:
        candles = [
            Candle("BTC", "1m", 0, 59_999, 100, 90, 99, 100.5, 10),
            Candle("BTC", "1m", 180_000, 239_999, 100.5, 102, 100, 101.2, -1),
        ]
        report = validate_candle_sequence("BTC", "1m", candles)
        self.assertFalse(report.is_valid)
        self.assertIn("invalid_high_low", report.issues)
        self.assertIn("gap_detected", report.issues)
        self.assertIn("negative_volume", report.issues)


if __name__ == "__main__":
    unittest.main()
