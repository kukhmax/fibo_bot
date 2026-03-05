from pathlib import Path
import tempfile
import unittest

from core.features import TrainingDataset
from core.features import TrainingSample
from core.ml.artifacts import ModelArtifactStore
from core.ml.trainer import BaselineModelTrainer
from core.ml.training_pipeline import MlTrainingPipeline


def _sample(value: float, label: int, ts: int) -> TrainingSample:
    return TrainingSample(
        open_time_ms=ts,
        features={
            "ret_1": value,
            "range_pct": value,
            "body_pct": value,
            "sma_ratio": 1.0 + value,
            "volume": 1.0,
        },
        label=label,
    )


class _DatasetBuilderStub:
    def __init__(self, dataset: TrainingDataset) -> None:
        self.dataset = dataset
        self.calls = 0

    def build(self, candle_limit: int = 2000, label_horizon: int = 1, up_threshold: float = 0.0) -> TrainingDataset:
        self.calls += 1
        return self.dataset


class TestMlTraining(unittest.TestCase):
    def test_baseline_trainer_learns_simple_boundary(self) -> None:
        train = [_sample(-0.4, 0, 1), _sample(-0.2, 0, 2), _sample(0.2, 1, 3), _sample(0.4, 1, 4)]
        validation = [_sample(-0.3, 0, 5), _sample(0.3, 1, 6)]
        dataset = TrainingDataset(train=train, validation=validation)
        model, report = BaselineModelTrainer().train(dataset=dataset, epochs=80, learning_rate=0.2)
        self.assertGreaterEqual(report.train_accuracy, 0.75)
        self.assertGreaterEqual(report.validation_accuracy, 0.5)
        self.assertLess(model.predict_proba({"ret_1": -0.5}), 0.5)
        self.assertGreater(model.predict_proba({"ret_1": 0.5}), 0.5)

    def test_artifact_store_save_and_load(self) -> None:
        train = [_sample(-0.1, 0, 1), _sample(0.1, 1, 2)]
        dataset = TrainingDataset(train=train, validation=[])
        model, report = BaselineModelTrainer().train(dataset=dataset, epochs=30, learning_rate=0.2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.json"
            store = ModelArtifactStore(path)
            saved = store.save(model, report)
            loaded = store.load()
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.feature_names, saved.feature_names)
            self.assertEqual(len(loaded.weights), len(saved.weights))

    def test_training_pipeline_produces_artifact(self) -> None:
        dataset = TrainingDataset(
            train=[_sample(-0.4, 0, 1), _sample(0.4, 1, 2)],
            validation=[_sample(0.2, 1, 3)],
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = ModelArtifactStore(Path(tmp) / "baseline.json")
            pipeline = MlTrainingPipeline(
                dataset_builder=_DatasetBuilderStub(dataset),  # type: ignore[arg-type]
                artifact_store=store,
            )
            artifact = pipeline.run(epochs=40, learning_rate=0.2)
            self.assertGreaterEqual(artifact.train_size, 2)
            self.assertIsNotNone(store.load())


if __name__ == "__main__":
    unittest.main()
