from dataclasses import dataclass

from core.data.models import Candle
from core.ml.artifacts import ModelArtifactStore
from core.ml.model import BaselineProbabilityModel


@dataclass(frozen=True)
class MlInferenceResult:
    allow: bool
    probability: float
    reason: str


class MlSignalFilter:
    def __init__(
        self,
        artifact_store: ModelArtifactStore | None = None,
        min_probability: float = 0.55,
        short_window: int = 5,
        long_window: int = 20,
    ) -> None:
        self.artifact_store = artifact_store or ModelArtifactStore()
        self.min_probability = min_probability
        self.short_window = short_window
        self.long_window = long_window
        self._model: BaselineProbabilityModel | None = None
        self._load_model()

    def is_active(self) -> bool:
        return self._model is not None

    def evaluate(self, candles: list[Candle]) -> MlInferenceResult:
        if self._model is None:
            return MlInferenceResult(allow=True, probability=1.0, reason="Model not loaded")
        features = build_latest_features(candles, short_window=self.short_window, long_window=self.long_window)
        if features is None:
            return MlInferenceResult(allow=True, probability=1.0, reason="Not enough candles for inference")
        probability = self._model.predict_proba(features)
        allow = probability >= self.min_probability
        reason = "Accepted by ML filter" if allow else "Rejected by ML filter"
        return MlInferenceResult(allow=allow, probability=probability, reason=reason)

    def _load_model(self) -> None:
        artifact = self.artifact_store.load()
        if artifact is None:
            self._model = None
            return
        self._model = BaselineProbabilityModel(
            feature_names=artifact.feature_names,
            weights=artifact.weights,
            bias=artifact.bias,
        )


def build_latest_features(
    candles: list[Candle],
    short_window: int = 5,
    long_window: int = 20,
) -> dict[str, float] | None:
    ordered = sorted(candles, key=lambda item: item.open_time_ms)
    if len(ordered) < max(2, long_window):
        return None
    idx = len(ordered) - 1
    current = ordered[idx]
    prev = ordered[idx - 1]
    prev_close = max(abs(prev.close), 1e-9)
    open_price = max(abs(current.open), 1e-9)
    sma_short = _mean([c.close for c in ordered[idx - short_window + 1 : idx + 1]])
    sma_long = _mean([c.close for c in ordered[idx - long_window + 1 : idx + 1]])
    return {
        "ret_1": (current.close - prev.close) / prev_close,
        "range_pct": (current.high - current.low) / open_price,
        "body_pct": (current.close - current.open) / open_price,
        "sma_ratio": sma_short / max(abs(sma_long), 1e-9),
        "volume": current.volume,
    }


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
