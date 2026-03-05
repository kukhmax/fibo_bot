from pathlib import Path
import tempfile
import unittest

from core.data.models import Candle
from core.features import TrainingDataset
from core.features import TrainingSample
from core.ml.artifacts import ModelArtifactStore
from core.ml.inference import MlSignalFilter
from core.ml.inference import build_latest_features
from core.ml.trainer import BaselineModelTrainer


def _candle(ts: int, close: float, open_shift: float = 0.1) -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe="5m",
        open_time_ms=ts,
        close_time_ms=ts + 299_999,
        open=close - open_shift,
        high=close + 0.2,
        low=close - 0.2,
        close=close,
        volume=1.0,
    )


def _sample(value: float, label: int, ts: int) -> TrainingSample:
    return TrainingSample(
        open_time_ms=ts,
        features={
            "ret_1": value,
            "range_pct": abs(value),
            "body_pct": value,
            "sma_ratio": 1.0 + value,
            "volume": 1.0,
        },
        label=label,
    )


class TestMlInference(unittest.TestCase):
    def test_build_latest_features_returns_none_on_short_window(self) -> None:
        candles = [_candle(0, 100), _candle(300_000, 101)]
        features = build_latest_features(candles, short_window=5, long_window=20)
        self.assertIsNone(features)

    def test_signal_filter_uses_artifact_and_threshold(self) -> None:
        dataset = TrainingDataset(
            train=[_sample(-0.4, 0, 1), _sample(-0.3, 0, 2), _sample(0.3, 1, 3), _sample(0.5, 1, 4)],
            validation=[_sample(0.2, 1, 5)],
        )
        model, report = BaselineModelTrainer().train(dataset, epochs=100, learning_rate=0.2)
        candles = [_candle(i * 300_000, 100 + i * 0.2) for i in range(25)]
        with tempfile.TemporaryDirectory() as tmp:
            store = ModelArtifactStore(Path(tmp) / "model.json")
            store.save(model, report)
            allow_filter = MlSignalFilter(artifact_store=store, min_probability=0.5)
            block_filter = MlSignalFilter(artifact_store=store, min_probability=0.99)
            allow_result = allow_filter.evaluate(candles)
            block_result = block_filter.evaluate(candles)
            self.assertGreaterEqual(allow_result.probability, 0.0)
            self.assertLessEqual(allow_result.probability, 1.0)
            self.assertTrue(allow_result.allow)
            self.assertFalse(block_result.allow)


if __name__ == "__main__":
    unittest.main()
