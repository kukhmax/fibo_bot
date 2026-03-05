from dataclasses import dataclass

from core.data.models import Candle


@dataclass(frozen=True)
class LabeledPoint:
    open_time_ms: int
    label: int
    future_return: float


class BinaryOutcomeLabeler:
    def __init__(self, label_horizon: int = 1, up_threshold: float = 0.0) -> None:
        self.label_horizon = max(1, label_horizon)
        self.up_threshold = up_threshold

    def make_labels(self, candles: list[Candle]) -> dict[int, LabeledPoint]:
        ordered = sorted(candles, key=lambda item: item.open_time_ms)
        last_index = len(ordered) - self.label_horizon
        if last_index <= 0:
            return {}
        labels: dict[int, LabeledPoint] = {}
        for idx in range(0, last_index):
            current = ordered[idx]
            future = ordered[idx + self.label_horizon]
            base = max(abs(current.close), 1e-9)
            future_return = (future.close - current.close) / base
            label = 1 if future_return > self.up_threshold else 0
            labels[current.open_time_ms] = LabeledPoint(
                open_time_ms=current.open_time_ms,
                label=label,
                future_return=future_return,
            )
        return labels
