import unittest

from core.data.models import Candle
from core.features import FeatureDatasetBuilder


def _candle(ts: int, close: float, volume: float = 1.0) -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe="5m",
        open_time_ms=ts,
        close_time_ms=ts + 299_999,
        open=close - 0.1,
        high=close + 0.2,
        low=close - 0.2,
        close=close,
        volume=volume,
    )


class TestFeatureDatasetBuilder(unittest.TestCase):
    def test_builds_train_and_validation_samples(self) -> None:
        candles = [_candle(i * 300_000, 100 + i, volume=1 + i) for i in range(25)]
        builder = FeatureDatasetBuilder(short_window=3, long_window=5, validation_ratio=0.2)
        dataset = builder.build(candles, label_horizon=1)
        self.assertGreater(len(dataset.train), 0)
        self.assertGreater(len(dataset.validation), 0)
        sample = dataset.train[0]
        self.assertIn("ret_1", sample.features)
        self.assertIn("range_pct", sample.features)
        self.assertIn("body_pct", sample.features)
        self.assertIn("sma_ratio", sample.features)
        self.assertIn("volume", sample.features)
        self.assertIn(sample.label, {0, 1})

    def test_returns_empty_when_not_enough_candles(self) -> None:
        candles = [_candle(i * 300_000, 100 + i) for i in range(4)]
        builder = FeatureDatasetBuilder(short_window=3, long_window=5, validation_ratio=0.2)
        dataset = builder.build(candles, label_horizon=1)
        self.assertEqual(dataset.train, [])
        self.assertEqual(dataset.validation, [])


if __name__ == "__main__":
    unittest.main()
