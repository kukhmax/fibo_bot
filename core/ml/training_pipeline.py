from core.ml.artifacts import BaselineModelArtifact
from core.ml.artifacts import ModelArtifactStore
from core.ml.dataset_builder import MlTrainDatasetBuilder
from core.ml.trainer import BaselineModelTrainer


class MlTrainingPipeline:
    def __init__(
        self,
        dataset_builder: MlTrainDatasetBuilder,
        trainer: BaselineModelTrainer | None = None,
        artifact_store: ModelArtifactStore | None = None,
    ) -> None:
        self.dataset_builder = dataset_builder
        self.trainer = trainer or BaselineModelTrainer()
        self.artifact_store = artifact_store or ModelArtifactStore()

    def run(
        self,
        candle_limit: int = 2000,
        label_horizon: int = 1,
        up_threshold: float = 0.0,
        epochs: int = 60,
        learning_rate: float = 0.1,
    ) -> BaselineModelArtifact:
        dataset = self.dataset_builder.build(
            candle_limit=candle_limit,
            label_horizon=label_horizon,
            up_threshold=up_threshold,
        )
        model, report = self.trainer.train(
            dataset=dataset,
            epochs=epochs,
            learning_rate=learning_rate,
        )
        return self.artifact_store.save(model, report)
