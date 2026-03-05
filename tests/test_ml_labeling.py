import unittest

from core.data.models import Candle
from core.ml import BinaryOutcomeLabeler
from core.ml import split_train_validation


def _candle(ts: int, close: float) -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe="5m",
        open_time_ms=ts,
        close_time_ms=ts + 299_999,
        open=close - 0.1,
        high=close + 0.2,
        low=close - 0.2,
        close=close,
        volume=1.0,
    )


class TestMlLabeling(unittest.TestCase):
    def test_binary_outcome_labeler_assigns_labels(self) -> None:
        candles = [_candle(0, 100), _candle(300_000, 101), _candle(600_000, 99)]
        labels = BinaryOutcomeLabeler(label_horizon=1, up_threshold=0.0).make_labels(candles)
        self.assertEqual(labels[0].label, 1)
        self.assertEqual(labels[300_000].label, 0)

    def test_split_train_validation(self) -> None:
        values = [1, 2, 3, 4, 5]
        train, validation = split_train_validation(values, validation_ratio=0.4)
        self.assertEqual(train, [1, 2, 3])
        self.assertEqual(validation, [4, 5])


if __name__ == "__main__":
    unittest.main()
