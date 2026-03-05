import unittest

from core.data.models import Candle
from core.ml.dataset_builder import MlTrainDatasetBuilder


def _candle(ts: int, close: float) -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe="5m",
        open_time_ms=ts,
        close_time_ms=ts + 299_999,
        open=close - 0.2,
        high=close + 0.3,
        low=close - 0.3,
        close=close,
        volume=2.0,
    )


class _HistoryStub:
    def __init__(self, candles: list[Candle]) -> None:
        self._candles = candles
        self.last_limit = None

    def build(self, limit: int = 2000) -> list[Candle]:
        self.last_limit = limit
        return self._candles[-limit:]


class TestMlDatasetBuilder(unittest.TestCase):
    def test_builds_dataset_from_history_pipeline(self) -> None:
        history = _HistoryStub([_candle(i * 300_000, 100 + i) for i in range(30)])
        builder = MlTrainDatasetBuilder(history_pipeline=history)  # type: ignore[arg-type]
        dataset = builder.build(candle_limit=30, label_horizon=1)
        self.assertEqual(history.last_limit, 30)
        self.assertGreater(len(dataset.train), 0)
        self.assertGreaterEqual(len(dataset.validation), 0)


if __name__ == "__main__":
    unittest.main()
