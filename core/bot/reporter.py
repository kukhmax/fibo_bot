from datetime import datetime, timezone

from core.backtest import MiniBacktestRunReport
from core.bot.profile import TelegramUserProfile
from core.ml.artifacts import ModelArtifactStore


class PositionReporter:
    def build_report(self, profile: TelegramUserProfile) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        pairs_text = ", ".join(f"{pair.symbol}:{pair.timeframe}" for pair in profile.trading_pairs)
        positions_line = (
            "✅ Нет открытых позиций\n" if profile.open_positions_count == 0 else "⚠️ Есть открытые позиции\n"
        )
        return (
            "📍 Отчет по позициям\n"
            + "━━━━━━━━━━━━━━\n"
            + f"🤖 Режим: {profile.mode}\n"
            + f"📈 Биржа: {profile.exchange}\n"
            + f"⏱ Таймфрейм: {profile.timeframe}\n"
            + f"🧩 Пары: {pairs_text}\n"
            + f"🛡 Риск: {profile.risk_per_trade_pct}%\n"
            + f"🎯 RR: {profile.rr_ratio}\n"
            + f"🚫 DD: {profile.max_daily_drawdown_pct}%\n"
            + f"📦 Макс. позиций: {profile.max_open_positions}\n"
            + f"🧯 SL: {profile.sl_pct}%\n"
            + f"💰 TP: {profile.tp_pct}%\n"
            + f"📌 Открытых позиций: {profile.open_positions_count}\n"
            + positions_line
            + f"🕒 Время: {now}"
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


class MiniBacktestReporter:
    def build_report(
        self,
        symbol: str,
        timeframe: str,
        candles_local_before: int,
        candles_loaded: int,
        remote_fetch: str,
        report: MiniBacktestRunReport,
    ) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        regime_summary = self._summary(report.regime_counts)
        strategy_summary = self._summary(report.strategy_entry_counts)
        return (
            "Mini-backtest отчет\n"
            f"[Параметры]\n"
            f"symbol={symbol}\n"
            f"timeframe={timeframe}\n"
            f"candles_local_before={candles_local_before}\n"
            f"candles_loaded={candles_loaded}\n"
            f"remote_fetch={remote_fetch}\n"
            f"[Сигналы]\n"
            f"signals_total={report.entries_total}\n"
            f"signals_after_ml={report.entries_after_ml}\n"
            f"signals_blocked_ml={report.entries_blocked_ml}\n"
            f"[Метрики]\n"
            f"trades={report.trades}\n"
            f"winrate={report.winrate:.4f}\n"
            f"pf={report.profit_factor:.4f}\n"
            f"max_dd_r={report.max_drawdown_r:.4f}\n"
            f"avg_rr={report.avg_rr:.4f}\n"
            f"expectancy_r={report.expectancy_r:.4f}\n"
            f"[Итог]\n"
            f"asset_status={'допущен' if report.is_allowed else 'не допущен'}\n"
            f"decision_reason={report.decision_reason}\n"
            f"[Распределения]\n"
            f"regimes={regime_summary}\n"
            f"strategies={strategy_summary}\n"
            f"ts={now}"
        )

    def _summary(self, payload: dict[str, int]) -> str:
        if not payload:
            return "none"
        return ",".join(f"{key}:{value}" for key, value in sorted(payload.items(), key=lambda item: item[0]))
