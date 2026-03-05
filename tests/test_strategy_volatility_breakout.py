import unittest

from core.strategies import VolatilityBreakoutStrategy
from core.data.models import Candle


def candle(o, h, l, c):
    return Candle(symbol="X", timeframe="5m", open_time_ms=0, close_time_ms=0, open=o, high=h, low=l, close=c, volume=0)


class TestVolatilityBreakout(unittest.TestCase):
    def test_buy_on_breakout_above_prev_high(self) -> None:
        s = VolatilityBreakoutStrategy()
        first = s.on_candle(candle(10, 12, 9, 11))
        self.assertEqual(first.action, "skip")
        sig = s.on_candle(candle(11, 13, 10, 12.5))
        self.assertEqual(sig.action, "entry")
        self.assertEqual(sig.direction, "BUY")
        self.assertTrue(sig.explain)

    def test_sell_on_breakout_below_prev_low(self) -> None:
        s = VolatilityBreakoutStrategy()
        self.assertEqual(s.on_candle(candle(10, 12, 9, 11)).action, "skip")
        sig = s.on_candle(candle(11, 11.5, 8.5, 8.8))
        self.assertEqual(sig.action, "entry")
        self.assertEqual(sig.direction, "SELL")


if __name__ == "__main__":
    unittest.main()
