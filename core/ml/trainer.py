from dataclasses import dataclass

from core.features import TrainingDataset
from core.features import TrainingSample
from core.ml.model import BaselineProbabilityModel


@dataclass(frozen=True)
class TrainingReport:
    train_accuracy: float
    validation_accuracy: float
    train_size: int
    validation_size: int


class BaselineModelTrainer:
    def __init__(self, feature_names: tuple[str, ...] | None = None) -> None:
        self.feature_names = feature_names or ("ret_1", "range_pct", "body_pct", "sma_ratio", "volume")

    def train(
        self,
        dataset: TrainingDataset,
        epochs: int = 60,
        learning_rate: float = 0.1,
    ) -> tuple[BaselineProbabilityModel, TrainingReport]:
        weights = [0.0 for _ in self.feature_names]
        bias = 0.0
        train_samples = dataset.train
        if not train_samples:
            model = BaselineProbabilityModel(self.feature_names, tuple(weights), bias)
            report = TrainingReport(0.0, 0.0, 0, len(dataset.validation))
            return model, report
        for _ in range(max(1, epochs)):
            for sample in train_samples:
                pred = _predict(weights, bias, self.feature_names, sample.features)
                error = pred - float(sample.label)
                for idx, feature_name in enumerate(self.feature_names):
                    value = float(sample.features.get(feature_name, 0.0))
                    weights[idx] -= learning_rate * error * value
                bias -= learning_rate * error
        model = BaselineProbabilityModel(self.feature_names, tuple(weights), bias)
        train_accuracy = _accuracy(model, train_samples)
        validation_accuracy = _accuracy(model, dataset.validation) if dataset.validation else train_accuracy
        report = TrainingReport(
            train_accuracy=train_accuracy,
            validation_accuracy=validation_accuracy,
            train_size=len(dataset.train),
            validation_size=len(dataset.validation),
        )
        return model, report


def _predict(weights: list[float], bias: float, names: tuple[str, ...], features: dict[str, float]) -> float:
    z = bias
    for idx, feature_name in enumerate(names):
        z += weights[idx] * float(features.get(feature_name, 0.0))
    if z > 40:
        return 1.0
    if z < -40:
        return 0.0
    exp = 2.718281828459045 ** (-z)
    return 1.0 / (1.0 + exp)


def _accuracy(model: BaselineProbabilityModel, samples: list[TrainingSample]) -> float:
    if not samples:
        return 0.0
    ok = 0
    for sample in samples:
        pred = 1 if model.predict_proba(sample.features) >= 0.5 else 0
        if pred == sample.label:
            ok += 1
    return ok / len(samples)
