import unittest

from core.strategies.liquidity_sweep_reversal import LiquiditySweepReversalStrategy
from core.data.models import Candle


def c(o, h, l, c_):
    return Candle(symbol="X", timeframe="5m", open_time_ms=0, close_time_ms=0, open=o, high=h, low=l, close=c_, volume=0)


class TestLiquiditySweepReversal(unittest.TestCase):
    def test_buy_after_sweep_below_prev_low(self) -> None:
        s = LiquiditySweepReversalStrategy()
        self.assertIsNone(s.on_candle(c(10, 12, 9, 10.5)))
        sig = s.on_candle(c(10, 11, 8.5, 10.8))
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, "BUY")

    def test_sell_after_sweep_above_prev_high(self) -> None:
        s = LiquiditySweepReversalStrategy()
        self.assertIsNone(s.on_candle(c(10, 12, 9, 11.5)))
        sig = s.on_candle(c(11.5, 12.6, 10.8, 11.0))
        self.assertIsNotNone(sig)
        self.assertEqual(sig.direction, "SELL")


if __name__ == "__main__":
    unittest.main()
