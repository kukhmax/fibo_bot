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
            return (
                "🧠 **ML отчет**\n"
                "━━━━━━━━━━━━━━━━\n"
                "⚠️ Модель не найдена.\n"
                "Система использует базовую стратегию без ML-фильтрации.\n\n"
                "👇 Нажми **«🚀 Обучить модель»**, чтобы запустить процесс обучения.\n"
                f"🕒 {now}"
            )
        return (
            "🧠 **ML отчет**\n"
            "━━━━━━━━━━━━━━━━\n"
            f"🎯 **Точность (Accuracy)**\n"
            f"Train: {artifact.train_accuracy:.2%}\n"
            f"Validation: {artifact.validation_accuracy:.2%}\n\n"
            f"📊 **Данные**\n"
            f"Train samples: {artifact.train_size}\n"
            f"Validation samples: {artifact.validation_size}\n\n"
            f"🎛 **Признаки (Features)**\n"
            f"{', '.join(artifact.feature_names)}\n\n"
            f"🕒 {now}"
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
            "🧪 Mini-Backtest отчет\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📌 **Параметры**\n"
            f"Symbol: {symbol}\n"
            f"Timeframe: {timeframe}\n"
            f"Candles: {candles_loaded} (Local: {candles_local_before})\n"
            f"Fetch: {remote_fetch}\n\n"
            f"📊 **Сигналы**\n"
            f"Total: {report.entries_total}\n"
            f"After ML: {report.entries_after_ml}\n"
            f"Blocked: {report.entries_blocked_ml}\n\n"
            f"📈 **Метрики**\n"
            f"Trades: {report.trades}\n"
            f"Winrate: {report.winrate:.2%}\n"
            f"Profit Factor: {report.profit_factor:.2f}\n"
            f"Max Drawdown (R): {report.max_drawdown_r:.2f}R\n"
            f"Avg RR: {report.avg_rr:.2f}\n"
            f"Expectancy: {report.expectancy_r:.2f}R\n\n"
            f"🏁 **Итог**\n"
            f"Status: {'✅ ДОПУЩЕН' if report.is_allowed else '❌ НЕ ДОПУЩЕН'}\n"
            f"Reason: {report.decision_reason}\n\n"
            f"🕒 {now}"
        )

    def _summary(self, payload: dict[str, int]) -> str:
        if not payload:
            return "none"
        return ",".join(f"{key}:{value}" for key, value in sorted(payload.items(), key=lambda item: item[0]))
