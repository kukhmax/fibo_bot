import unittest

from core.data import CandleBuilder
from core.data import Tick


class TestCandleBuilder(unittest.TestCase):
    def test_aggregates_ticks_into_candle(self) -> None:
        builder = CandleBuilder(symbol="BTC", timeframe="1m")

        closed = builder.add_tick(Tick(symbol="BTC", timestamp_ms=1_000, price=100.0, volume=1.2))
        self.assertEqual(closed, [])
        closed = builder.add_tick(Tick(symbol="BTC", timestamp_ms=20_000, price=102.0, volume=0.3))
        self.assertEqual(closed, [])
        closed = builder.add_tick(Tick(symbol="BTC", timestamp_ms=61_000, price=101.0, volume=0.5))

        self.assertEqual(len(closed), 1)
        candle = closed[0]
        self.assertEqual(candle.open, 100.0)
        self.assertEqual(candle.high, 102.0)
        self.assertEqual(candle.low, 100.0)
        self.assertEqual(candle.close, 102.0)
        self.assertAlmostEqual(candle.volume, 1.5)

    def test_rejects_unexpected_symbol(self) -> None:
        builder = CandleBuilder(symbol="BTC", timeframe="1m")
        with self.assertRaises(ValueError):
            builder.add_tick(Tick(symbol="ETH", timestamp_ms=1_000, price=100.0, volume=1.0))


if __name__ == "__main__":
    unittest.main()
