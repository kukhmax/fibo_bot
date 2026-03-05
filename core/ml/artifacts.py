from dataclasses import asdict
from dataclasses import dataclass
import json
from pathlib import Path

from core.ml.model import BaselineProbabilityModel
from core.ml.trainer import TrainingReport


@dataclass(frozen=True)
class BaselineModelArtifact:
    feature_names: tuple[str, ...]
    weights: tuple[float, ...]
    bias: float
    train_accuracy: float
    validation_accuracy: float
    train_size: int
    validation_size: int


class ModelArtifactStore:
    def __init__(self, file_path: str | Path = "runtime/ml/baseline_model.json") -> None:
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, model: BaselineProbabilityModel, report: TrainingReport) -> BaselineModelArtifact:
        artifact = BaselineModelArtifact(
            feature_names=model.feature_names,
            weights=model.weights,
            bias=model.bias,
            train_accuracy=report.train_accuracy,
            validation_accuracy=report.validation_accuracy,
            train_size=report.train_size,
            validation_size=report.validation_size,
        )
        payload = asdict(artifact)
        self.file_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return artifact

    def load(self) -> BaselineModelArtifact | None:
        if not self.file_path.exists():
            return None
        payload = json.loads(self.file_path.read_text(encoding="utf-8"))
        return BaselineModelArtifact(
            feature_names=tuple(payload["feature_names"]),
            weights=tuple(payload["weights"]),
            bias=float(payload["bias"]),
            train_accuracy=float(payload["train_accuracy"]),
            validation_accuracy=float(payload["validation_accuracy"]),
            train_size=int(payload["train_size"]),
            validation_size=int(payload["validation_size"]),
        )
