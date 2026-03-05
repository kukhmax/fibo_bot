from dataclasses import dataclass

from core.data.models import Candle


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
        min_index = max(1, self.long_window - 1)
        last_index = len(ordered) - label_horizon
        if last_index <= min_index:
            return TrainingDataset(train=[], validation=[])
        samples: list[TrainingSample] = []
        for idx in range(min_index, last_index):
            current = ordered[idx]
            prev = ordered[idx - 1]
            future = ordered[idx + label_horizon]
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
            target_price = current.close * (1.0 + up_threshold)
            label = 1 if future.close > target_price else 0
            samples.append(TrainingSample(open_time_ms=current.open_time_ms, features=feature_row, label=label))
        return _split_dataset(samples, self.validation_ratio)


def _split_dataset(samples: list[TrainingSample], validation_ratio: float) -> TrainingDataset:
    if not samples:
        return TrainingDataset(train=[], validation=[])
    split_at = int(len(samples) * (1.0 - validation_ratio))
    split_at = max(1, min(split_at, len(samples)))
    return TrainingDataset(train=samples[:split_at], validation=samples[split_at:])


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
