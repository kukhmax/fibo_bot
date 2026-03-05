from dataclasses import dataclass
import math


@dataclass(frozen=True)
class BaselineProbabilityModel:
    feature_names: tuple[str, ...]
    weights: tuple[float, ...]
    bias: float

    def predict_proba(self, features: dict[str, float]) -> float:
        z = self.bias
        for idx, feature_name in enumerate(self.feature_names):
            z += self.weights[idx] * float(features.get(feature_name, 0.0))
        z = max(-40.0, min(40.0, z))
        return 1.0 / (1.0 + math.exp(-z))
