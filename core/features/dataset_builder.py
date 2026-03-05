from dataclasses import dataclass

from core.data.models import Candle
from core.ml.labeling import BinaryOutcomeLabeler
from core.ml.train_validation import split_train_validation


@dataclass(frozen=True)
class TrainingSample:
    open_time_ms: int
    features: dict[str, float]
    label: int


@dataclass(frozen=True)
class TrainingDataset:
    train: list[TrainingSample]
    validation: list[TrainingSample]


class FeatureDatasetBuilder:
    def __init__(self, short_window: int = 5, long_window: int = 20, validation_ratio: float = 0.2) -> None:
        self.short_window = short_window
        self.long_window = long_window
        self.validation_ratio = validation_ratio

    def build(self, candles: list[Candle], label_horizon: int = 1, up_threshold: float = 0.0) -> TrainingDataset:
        ordered = sorted(candles, key=lambda item: item.open_time_ms)
        labels = BinaryOutcomeLabeler(label_horizon=label_horizon, up_threshold=up_threshold).make_labels(ordered)
        min_index = max(1, self.long_window - 1)
        if len(ordered) <= min_index:
            return TrainingDataset(train=[], validation=[])
        samples: list[TrainingSample] = []
        for idx in range(min_index, len(ordered)):
            current = ordered[idx]
            labeled = labels.get(current.open_time_ms)
            if labeled is None:
                continue
            prev = ordered[idx - 1]
            prev_close = max(abs(prev.close), 1e-9)
            open_price = max(abs(current.open), 1e-9)
            sma_short = _mean([c.close for c in ordered[idx - self.short_window + 1 : idx + 1]])
            sma_long = _mean([c.close for c in ordered[idx - self.long_window + 1 : idx + 1]])
            feature_row = {
                "ret_1": (current.close - prev.close) / prev_close,
                "range_pct": (current.high - current.low) / open_price,
                "body_pct": (current.close - current.open) / open_price,
                "sma_ratio": sma_short / max(abs(sma_long), 1e-9),
                "volume": current.volume,
            }
            samples.append(TrainingSample(open_time_ms=current.open_time_ms, features=feature_row, label=labeled.label))
        train, validation = split_train_validation(samples, self.validation_ratio)
        return TrainingDataset(train=train, validation=validation)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
