import unittest

from core.data.models import Candle
from core.ml import HistoricalTrainingDataPipeline


def _candle(ts: int, close: float) -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe="5m",
        open_time_ms=ts,
        close_time_ms=ts + 299_999,
        open=close - 0.2,
        high=close + 0.2,
        low=close - 0.4,
        close=close,
        volume=1.0,
    )


class _LocalStub:
    def __init__(self, candles: list[Candle]) -> None:
        self._candles = candles

    def load(self, symbol: str, timeframe: str, limit: int | None = None) -> list[Candle]:
        selected = [c for c in self._candles if c.symbol == symbol and c.timeframe == timeframe]
        if limit is not None:
            return selected[-limit:]
        return selected


class _RemoteStub:
    def __init__(self, candles: list[Candle]) -> None:
        self._candles = candles
        self.calls = 0

    def fetch_with_fallback(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        self.calls += 1
        selected = [c for c in self._candles if c.symbol == symbol and c.timeframe == timeframe]
        return selected[-limit:]


class TestHistoricalTrainingDataPipeline(unittest.TestCase):
    def test_uses_only_local_when_enough_candles(self) -> None:
        local = _LocalStub([_candle(0, 100.0), _candle(300_000, 101.0), _candle(600_000, 102.0)])
        remote = _RemoteStub([_candle(-300_000, 99.0)])
        pipeline = HistoricalTrainingDataPipeline(
            symbol="BTCUSDT",
            timeframe="5m",
            min_candles=3,
            local_history=local,  # type: ignore[arg-type]
            historical_data=remote,  # type: ignore[arg-type]
        )
        candles = pipeline.build(limit=10)
        self.assertEqual(len(candles), 3)
        self.assertEqual(remote.calls, 0)

    def test_fetches_remote_and_merges_with_dedup(self) -> None:
        local = _LocalStub([_candle(300_000, 101.0), _candle(600_000, 102.0)])
        remote = _RemoteStub([_candle(0, 100.0), _candle(300_000, 100.5)])
        pipeline = HistoricalTrainingDataPipeline(
            symbol="BTCUSDT",
            timeframe="5m",
            min_candles=4,
            local_history=local,  # type: ignore[arg-type]
            historical_data=remote,  # type: ignore[arg-type]
        )
        candles = pipeline.build(limit=10)
        self.assertEqual(remote.calls, 1)
        self.assertEqual([c.open_time_ms for c in candles], [0, 300_000, 600_000])
        self.assertEqual(candles[1].close, 101.0)

    def test_applies_limit_to_tail(self) -> None:
        local = _LocalStub([_candle(0, 100), _candle(300_000, 101), _candle(600_000, 102)])
        remote = _RemoteStub([_candle(-300_000, 99)])
        pipeline = HistoricalTrainingDataPipeline(
            symbol="BTCUSDT",
            timeframe="5m",
            min_candles=4,
            local_history=local,  # type: ignore[arg-type]
            historical_data=remote,  # type: ignore[arg-type]
        )
        candles = pipeline.build(limit=2)
        self.assertEqual([c.open_time_ms for c in candles], [300_000, 600_000])


if __name__ == "__main__":
    unittest.main()
