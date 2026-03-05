import unittest

from core.data.models import Candle
from core.regime import RuleBasedRegimeClassifier


def _candle(ts: int, o: float, h: float, l: float, c: float) -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe="5m",
        open_time_ms=ts,
        close_time_ms=ts + 299999,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=1.0,
    )


class TestRegimeClassifier(unittest.TestCase):
    def setUp(self) -> None:
        self._clf = RuleBasedRegimeClassifier()

    def test_returns_unknown_on_short_window(self) -> None:
        result = self._clf.classify([_candle(0, 100, 101, 99, 100.5)])
        self.assertEqual(result.label, "unknown")

    def test_detects_trend_up(self) -> None:
        candles = [
            _candle(0, 100, 101, 99.5, 100.4),
            _candle(1, 100.4, 101.3, 100.0, 100.9),
            _candle(2, 100.9, 101.8, 100.5, 101.4),
            _candle(3, 101.4, 102.2, 101.0, 101.9),
            _candle(4, 101.9, 102.7, 101.5, 102.4),
        ]
        result = self._clf.classify(candles)
        self.assertEqual(result.label, "trend_up")

    def test_detects_trend_down(self) -> None:
        candles = [
            _candle(0, 102.5, 102.8, 101.9, 102.2),
            _candle(1, 102.2, 102.4, 101.3, 101.8),
            _candle(2, 101.8, 102.0, 100.9, 101.4),
            _candle(3, 101.4, 101.6, 100.4, 100.9),
            _candle(4, 100.9, 101.1, 99.9, 100.3),
        ]
        result = self._clf.classify(candles)
        self.assertEqual(result.label, "trend_down")

    def test_detects_volatile(self) -> None:
        candles = [
            _candle(0, 100, 104, 96, 101),
            _candle(1, 101, 107, 95, 99),
            _candle(2, 99, 106, 92, 103),
            _candle(3, 103, 109, 97, 98),
            _candle(4, 98, 105, 90, 102),
        ]
        result = self._clf.classify(candles)
        self.assertEqual(result.label, "volatile")

    def test_detects_range(self) -> None:
        candles = [
            _candle(0, 100, 100.6, 99.6, 100.2),
            _candle(1, 100.2, 100.7, 99.7, 100.0),
            _candle(2, 100.0, 100.5, 99.6, 100.1),
            _candle(3, 100.1, 100.6, 99.7, 99.9),
            _candle(4, 99.9, 100.4, 99.5, 100.0),
        ]
        result = self._clf.classify(candles)
        self.assertEqual(result.label, "range")


if __name__ == "__main__":
    unittest.main()
