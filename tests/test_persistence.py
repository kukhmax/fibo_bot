from pathlib import Path
import tempfile
import unittest

from core.backtest import load_local_backtest_candles
from core.data import Candle
from core.data import LocalCandleHistory
from core.data import RealtimeCandlePipeline
from core.data import StateCache


class TestPersistence(unittest.IsolatedAsyncioTestCase):
    async def test_state_cache_set_and_get(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = StateCache(Path(tmp) / "state.json")
            cache.set("last_open", 60_000)
            restored = StateCache(Path(tmp) / "state.json")
            self.assertEqual(restored.get("last_open"), 60_000)

    async def test_local_history_append_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history = LocalCandleHistory(Path(tmp) / "history")
            history.append(Candle("BTC", "1m", 0, 59_999, 100, 101, 99, 100, 1.0))
            history.append(Candle("BTC", "1m", 60_000, 119_999, 100, 102, 99, 101, 2.0))
            loaded = history.load("BTC", "1m", limit=1)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].open_time_ms, 60_000)

    async def test_pipeline_restores_last_emitted_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = StateCache(Path(tmp) / "state.json")
            history = LocalCandleHistory(Path(tmp) / "history")
            first_emitted: list[Candle] = []
            pipeline1 = RealtimeCandlePipeline(
                symbol="BTC",
                timeframe="1m",
                on_candle=lambda candle: first_emitted.append(candle),
                state_cache=cache,
                local_history=history,
            )
            await pipeline1.process_backfill([Candle("BTC", "1m", 60_000, 119_999, 100, 102, 99, 101, 1.0)])

            second_emitted: list[Candle] = []
            pipeline2 = RealtimeCandlePipeline(
                symbol="BTC",
                timeframe="1m",
                on_candle=lambda candle: second_emitted.append(candle),
                state_cache=StateCache(Path(tmp) / "state.json"),
                local_history=LocalCandleHistory(Path(tmp) / "history"),
            )
            await pipeline2.process_backfill(
                [
                    Candle("BTC", "1m", 60_000, 119_999, 100, 102, 99, 101, 1.0),
                    Candle("BTC", "1m", 120_000, 179_999, 101, 103, 100, 102, 1.5),
                ]
            )

            self.assertEqual(len(first_emitted), 1)
            self.assertEqual(len(second_emitted), 1)
            self.assertEqual(second_emitted[0].open_time_ms, 120_000)

    async def test_backtest_loader_reads_local_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history = LocalCandleHistory(Path(tmp) / "history")
            history.append(Candle("BTC", "1m", 0, 59_999, 100, 101, 99, 100, 1.0))
            loaded = load_local_backtest_candles("BTC", "1m", history_dir=Path(tmp) / "history")
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].close, 100.0)


if __name__ == "__main__":
    unittest.main()
