from datetime import datetime, timezone

from core.bot.profile import TelegramUserProfile
from core.ml.artifacts import ModelArtifactStore


class PositionReporter:
    def build_report(self, profile: TelegramUserProfile) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return (
            "Отчет по позициям\n"
            f"mode={profile.mode} exchange={profile.exchange} timeframe={profile.timeframe}\n"
            f"risk={profile.risk_per_trade_pct} rr={profile.rr_ratio} max_dd={profile.max_daily_drawdown_pct} max_pos={profile.max_open_positions}\n"
            "Нет открытых позиций\n"
            f"ts={now}"
        )


class MlQualityReporter:
    def __init__(self, artifact_store: ModelArtifactStore | None = None) -> None:
        self.artifact_store = artifact_store or ModelArtifactStore()

    def build_report(self) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        artifact = self.artifact_store.load()
        if artifact is None:
            return "ML отчет\nartifact=not_found\nЗапусти обучение модели (/ml_train в следующих этапах)\n" f"ts={now}"
        return (
            "ML отчет\n"
            f"train_accuracy={artifact.train_accuracy:.4f}\n"
            f"validation_accuracy={artifact.validation_accuracy:.4f}\n"
            f"train_size={artifact.train_size} validation_size={artifact.validation_size}\n"
            f"features={','.join(artifact.feature_names)}\n"
            f"ts={now}"
        )
