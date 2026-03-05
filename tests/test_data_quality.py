import unittest

from core.data import Candle
from core.data import RuntimeDataQualityMonitor
from core.data import Tick
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

    def test_runtime_monitor_detects_gap_and_stale(self) -> None:
        now = {"value": 120_000}
        monitor = RuntimeDataQualityMonitor(
            symbol="BTC",
            timeframe="1m",
            stale_timeout_ms=15_000,
            clock_ms=lambda: now["value"],
        )
        monitor.evaluate_tick(Tick("BTC", 10_000, 100.0, 1.0))
        first = monitor.evaluate_candle(Candle("BTC", "1m", 0, 59_999, 100, 101, 99, 100.5, 1.0))
        second = monitor.evaluate_candle(Candle("BTC", "1m", 180_000, 239_999, 100, 101, 99, 100.5, 1.0))
        stale = monitor.evaluate_staleness()

        self.assertTrue(first.is_valid)
        self.assertIn("gap_detected", second.issues)
        self.assertIn("stale_stream", stale.issues)

    def test_runtime_monitor_detects_timestamp_drift(self) -> None:
        monitor = RuntimeDataQualityMonitor(
            symbol="BTC",
            timeframe="1m",
            max_timestamp_drift_ms=1_000,
            clock_ms=lambda: 10_000,
        )
        tick_report = monitor.evaluate_tick(Tick("BTC", 12_500, 100.0, 1.0))
        candle_report = monitor.evaluate_candle(
            Candle("BTC", "1m", 10_000, 14_000, 100, 101, 99, 100.5, 1.0)
        )

        self.assertIn("timestamp_drift", tick_report.issues)
        self.assertIn("timestamp_drift", candle_report.issues)


if __name__ == "__main__":
    unittest.main()
