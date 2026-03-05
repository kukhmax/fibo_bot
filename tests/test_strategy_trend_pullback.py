import unittest

from core.data.models import Candle
from core.strategies import TrendPullbackStrategy


def candle(close: float) -> Candle:
    return Candle(symbol="X", timeframe="5m", open_time_ms=0, close_time_ms=0, open=close, high=close, low=close, close=close, volume=0)


class TestTrendPullback(unittest.TestCase):
    def test_entry_buy_after_three_rising_closes(self) -> None:
        s = TrendPullbackStrategy()
        self.assertEqual(s.on_candle(candle(10)).action, "skip")
        self.assertEqual(s.on_candle(candle(11)).action, "skip")
        d = s.on_candle(candle(12))
        self.assertEqual(d.action, "entry")
        self.assertEqual(d.direction, "BUY")
        self.assertTrue(d.explain)

    def test_skip_when_no_monotonic_sequence(self) -> None:
        s = TrendPullbackStrategy()
        s.on_candle(candle(10))
        s.on_candle(candle(12))
        d = s.on_candle(candle(11))
        self.assertEqual(d.action, "skip")
        self.assertIsNone(d.direction)
        self.assertTrue(d.explain)


if __name__ == "__main__":
    unittest.main()
