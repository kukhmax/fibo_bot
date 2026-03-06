from pathlib import Path
import tempfile
import unittest

from core.backtest import load_backtest_candles
from core.data import Candle
from core.data import LocalCandleHistory


class _HistoricalStub:
    def __init__(self, candles: list[Candle]) -> None:
        self._candles = candles
        self.called = 0

    def fetch_with_fallback(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        self.called += 1
        return self._candles[-limit:]


class TestBacktestHistory(unittest.TestCase):
    def test_uses_local_only_when_enough_candles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history = LocalCandleHistory(Path(tmp) / "history")
            history.append(Candle("BTCUSDT", "1m", 0, 59_999, 100, 101, 99, 100, 1.0))
            history.append(Candle("BTCUSDT", "1m", 60_000, 119_999, 100, 102, 99, 101, 1.0))
            stub = _HistoricalStub(candles=[])
            candles = load_backtest_candles(
                symbol="BTCUSDT",
                timeframe="1m",
                limit=2,
                history_dir=Path(tmp) / "history",
                historical_data=stub,
            )
            self.assertEqual(len(candles), 2)
            self.assertEqual(stub.called, 0)

    def test_fetches_remote_and_merges_with_dedup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history = LocalCandleHistory(Path(tmp) / "history")
            history.append(Candle("BTCUSDT", "1m", 60_000, 119_999, 100, 102, 99, 101, 1.0))
            remote = [
                Candle("BTCUSDT", "1m", 0, 59_999, 99, 101, 98, 100, 1.0),
                Candle("BTCUSDT", "1m", 60_000, 119_999, 100, 102, 99, 101, 1.0),
            ]
            stub = _HistoricalStub(candles=remote)
            candles = load_backtest_candles(
                symbol="BTCUSDT",
                timeframe="1m",
                limit=2,
                history_dir=Path(tmp) / "history",
                historical_data=stub,
            )
            self.assertEqual(stub.called, 1)
            self.assertEqual(len(candles), 2)
            self.assertEqual(candles[0].open_time_ms, 0)
            self.assertEqual(candles[1].open_time_ms, 60_000)
            persisted = LocalCandleHistory(Path(tmp) / "history").load("BTCUSDT", "1m", limit=10)
            self.assertEqual(len(persisted), 2)


if __name__ == "__main__":
    unittest.main()
