import unittest

from core.data import Candle
from core.data import RealtimeCandlePipeline
from core.data import Tick


class TestRealtimeCandlePipeline(unittest.IsolatedAsyncioTestCase):
    async def test_default_timeframe_is_5m(self) -> None:
        emitted: list[Candle] = []
        pipeline = RealtimeCandlePipeline(symbol="BTC", on_candle=lambda candle: emitted.append(candle))
        self.assertEqual(pipeline.timeframe, "5m")

    async def test_emits_closed_candle_for_5m(self) -> None:
        emitted: list[Candle] = []
        pipeline = RealtimeCandlePipeline(symbol="BTC", timeframe="5m", on_candle=lambda candle: emitted.append(candle))

        await pipeline.process_tick(Tick(symbol="BTC", timestamp_ms=1_000, price=100.0, volume=1.0))
        await pipeline.process_tick(Tick(symbol="BTC", timestamp_ms=301_000, price=101.0, volume=0.5))

        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].timeframe, "5m")
        self.assertEqual(emitted[0].open, 100.0)
        self.assertEqual(emitted[0].close, 100.0)

    async def test_accepts_configurable_timeframe(self) -> None:
        emitted: list[Candle] = []
        pipeline = RealtimeCandlePipeline(symbol="BTC", timeframe="1m", on_candle=lambda candle: emitted.append(candle))

        await pipeline.process_tick(Tick(symbol="BTC", timestamp_ms=1_000, price=100.0, volume=1.0))
        await pipeline.process_tick(Tick(symbol="BTC", timestamp_ms=61_000, price=101.0, volume=0.2))

        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].timeframe, "1m")

    async def test_backfill_skips_duplicates(self) -> None:
        emitted: list[Candle] = []
        pipeline = RealtimeCandlePipeline(symbol="BTC", timeframe="1m", on_candle=lambda candle: emitted.append(candle))

        await pipeline.process_tick(Tick(symbol="BTC", timestamp_ms=1_000, price=100.0, volume=1.0))
        await pipeline.process_tick(Tick(symbol="BTC", timestamp_ms=61_000, price=101.0, volume=0.2))
        await pipeline.process_backfill(
            [
                Candle("BTC", "1m", 0, 59_999, 99, 102, 98, 100, 1),
                Candle("BTC", "1m", 60_000, 119_999, 100, 103, 99, 101, 1.2),
            ]
        )

        self.assertEqual(len(emitted), 2)
        self.assertEqual(emitted[1].open_time_ms, 60_000)


if __name__ == "__main__":
    unittest.main()
