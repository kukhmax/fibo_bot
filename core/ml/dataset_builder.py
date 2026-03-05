from core.features import FeatureDatasetBuilder
from core.features import TrainingDataset
from core.ml.history_pipeline import HistoricalTrainingDataPipeline


class MlTrainDatasetBuilder:
    def __init__(
        self,
        history_pipeline: HistoricalTrainingDataPipeline,
        feature_builder: FeatureDatasetBuilder | None = None,
    ) -> None:
        self.history_pipeline = history_pipeline
        self.feature_builder = feature_builder or FeatureDatasetBuilder()

    def build(
        self,
        candle_limit: int = 2000,
        label_horizon: int = 1,
        up_threshold: float = 0.0,
    ) -> TrainingDataset:
        candles = self.history_pipeline.build(limit=candle_limit)
        return self.feature_builder.build(candles, label_horizon=label_horizon, up_threshold=up_threshold)
