from argparse import ArgumentParser
import asyncio
from collections import deque
import json
import os
import sys

from core.bot.commands import build_default_router
from core.bot.alerts import RiskAlertNotifier
from core.bot.health import health_snapshot_dict
from core.bot.news_engine import NewsRiskGate
from core.bot.profile import TelegramUserProfileStore
from core.bot.runtime import TelegramBotRuntime
from core.bot.telegram_transport import TelegramApiTransport
from core.data.pipeline import RealtimeCandlePipeline
from core.ml.inference import MlSignalFilter
from core.regime import RuleBasedRegimeClassifier
from core.risk import DailyDrawdownGuard
from core.risk import RiskManager
from core.strategies import LiquiditySweepReversalStrategy
from core.strategies import TrendPullbackStrategy
from core.strategies import VolatilityBreakoutStrategy
from core.strategies import select_strategy_by_regime
from core.config import load_environment_config
from core.config import load_runtime_secrets


def run(once: bool = False, print_commands: bool = False) -> None:
    app_env = os.getenv("APP_ENV", "dev")
    config = load_environment_config(app_env)
    secrets = load_runtime_secrets()
    store = TelegramUserProfileStore()
    router = build_default_router(config, profile_store=store)

    print(
        f"fib_bot app started env={config.environment} mode={config.bot.mode} "
        f"primary_exchange={config.exchange.primary} token_configured={bool(secrets.telegram_bot_token)}"
    )
    if print_commands:
        print(json.dumps({"commands": router.available_commands()}, ensure_ascii=False))

    if print_commands and once:
        return
    if not secrets.telegram_bot_token:
        raise ValueError("Missing required secret: TELEGRAM_BOT_TOKEN")
    transport = TelegramApiTransport(bot_token=secrets.telegram_bot_token)
    runtime = TelegramBotRuntime(router=router, transport=transport, profile_store=store)
    asyncio.run(_run_app(runtime=runtime, transport=transport, store=store, config_env=config, once=once))


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--commands", action="store_true")
    args = parser.parse_args()
    if args.health:
        payload = health_snapshot_dict()
        print(json.dumps(payload, ensure_ascii=False))
        sys.exit(0 if payload["healthy"] else 1)
    run(once=args.once, print_commands=args.commands)


async def _run_runtime(runtime: TelegramBotRuntime, once: bool) -> None:
    if once:
        await runtime.process_once()
        return
    while True:
        processed = await runtime.process_once()
        if processed == 0:
            await asyncio.sleep(1)


async def _run_app(runtime: TelegramBotRuntime, transport: TelegramApiTransport, store: TelegramUserProfileStore, config_env, once: bool) -> None:  # type: ignore[no-untyped-def]
    if once:
        await _run_runtime(runtime, once=True)
        return
    enable_signals = bool(os.getenv("ENABLE_SIGNALS"))
    if not enable_signals:
        await _run_runtime(runtime, once=False)
        return
    symbol = os.getenv("FIB_SYMBOL", "BTCUSDT")
    timeframe = config_env.exchange.default_timeframe
    strategy_mode = os.getenv("FIB_STRATEGY", "auto_regime").strip().lower()
    strategies = {
        "trend_pullback": TrendPullbackStrategy(),
        "volatility_breakout": VolatilityBreakoutStrategy(),
        "liquidity_sweep": LiquiditySweepReversalStrategy(),
    }
    classifier = RuleBasedRegimeClassifier()
    regime_window = deque(maxlen=30)
    ml_window = deque(maxlen=60)
    ml_filter = MlSignalFilter(
        min_probability=float(os.getenv("ML_MIN_PROBA", "0.55")),
        short_window=int(os.getenv("ML_SHORT_WINDOW", "5")),
        long_window=int(os.getenv("ML_LONG_WINDOW", "20")),
    )
    ml_enabled = bool(config_env.ml.enabled)
    risk_manager = RiskManager()
    risk_alert_notifier = RiskAlertNotifier(cooldown_minutes=int(os.getenv("RISK_ALERT_COOLDOWN_MIN", "30")))
    drawdown_guard = DailyDrawdownGuard(
        max_daily_drawdown_pct=float(config_env.risk.max_daily_drawdown_pct),
        pause_until_utc_hour=int(config_env.risk.pause_until_utc_hour),
    )
    default_equity = float(os.getenv("PAPER_START_EQUITY", "1000"))
    whitelist_symbols = _parse_whitelist_symbols(os.getenv("WHITELIST_SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT"))
    min_avg_volume = float(os.getenv("WL_MIN_AVG_VOLUME", "50"))
    max_avg_spread_pct = float(os.getenv("WL_MAX_AVG_SPREAD_PCT", "5.0"))
    news_filter_enabled = bool(os.getenv("NEWS_FILTER_ENABLED", "1"))
    news_gate = NewsRiskGate(
        source=os.getenv("NEWS_SOURCE", "t.me/cryptoarsenal"),
        keywords=tuple(
            item.strip()
            for item in os.getenv(
                "NEWS_RISK_KEYWORDS",
                "hack,exploit,bankrupt,bankruptcy,liquidation,delist,lawsuit,outage",
            ).split(",")
            if item.strip()
        ),
        min_block_score=int(os.getenv("NEWS_BLOCK_MIN_SCORE", "1")),
    )

    async def on_candle(candle):
        regime_window.append(candle)
        ml_window.append(candle)
        regime = classifier.classify(list(regime_window))
        if strategy_mode in strategies:
            strategy_name = strategy_mode
        else:
            strategy_name = select_strategy_by_regime(regime.label, fallback="trend_pullback")
        decision = strategies[strategy_name].on_candle(candle)
        if decision.action != "entry":
            return
        if news_filter_enabled:
            headline = os.getenv("NEWS_HEADLINE", "")
            news_decision = news_gate.evaluate(headline)
            if news_decision.blocked:
                state = store._cache.load()
                for key, payload in state.items():
                    if not isinstance(key, str) or not key.startswith("profile:"):
                        continue
                    try:
                        user_id = int(key.split(":", 1)[1])
                    except Exception:
                        continue
                    mode = str(payload.get("mode", "signal_only")).lower()
                    if mode not in {"signal_only", "paper"}:
                        continue
                    transport.send_text(
                        chat_id=user_id,
                        text=f"risk_blocked: news_filter={news_decision.reason}",
                    )
                    risk_alert_notifier.maybe_send(
                        transport=transport,
                        chat_id=user_id,
                        user_id=user_id,
                        code="NEWS_FILTER_BLOCK",
                        details=news_decision.reason,
                    )
                return
        symbol_allowed, symbol_reason = _passes_asset_whitelist(
            symbol=str(candle.symbol),
            volume=float(candle.volume),
            high=float(candle.high),
            low=float(candle.low),
            close=float(candle.close),
            allowed_symbols=whitelist_symbols,
            min_volume=min_avg_volume,
            max_spread_pct=max_avg_spread_pct,
        )
        if not symbol_allowed:
            state = store._cache.load()
            for key, payload in state.items():
                if not isinstance(key, str) or not key.startswith("profile:"):
                    continue
                try:
                    user_id = int(key.split(":", 1)[1])
                except Exception:
                    continue
                mode = str(payload.get("mode", "signal_only")).lower()
                if mode not in {"signal_only", "paper"}:
                    continue
                transport.send_text(chat_id=user_id, text=f"risk_blocked: asset_filter={symbol_reason}")
                risk_alert_notifier.maybe_send(
                    transport=transport,
                    chat_id=user_id,
                    user_id=user_id,
                    code="ASSET_FILTER_BLOCK",
                    details=symbol_reason,
                )
            return
        ml_probability = 1.0
        if ml_enabled and ml_filter.is_active():
            inference = ml_filter.evaluate(list(ml_window))
            ml_probability = inference.probability
            if not inference.allow:
                return
        state = store._cache.load()
        for key, payload in state.items():
            if not isinstance(key, str) or not key.startswith("profile:"):
                continue
            try:
                user_id = int(key.split(":", 1)[1])
            except Exception:
                continue
            mode = str(payload.get("mode", "signal_only")).lower()
            if mode not in {"signal_only", "paper"}:
                continue
            raw_risk = payload.get("risk_per_trade_pct", config_env.risk.risk_per_trade_pct)
            try:
                risk_value = float(raw_risk)
            except Exception:
                risk_value = config_env.risk.risk_per_trade_pct
            risk_check = risk_manager.validate_risk_per_trade_pct(risk_value)
            if not risk_check.allowed:
                transport.send_text(chat_id=user_id, text=f"risk_blocked: {risk_check.reason}")
                risk_alert_notifier.maybe_send(
                    transport=transport,
                    chat_id=user_id,
                    user_id=user_id,
                    code="RISK_PER_TRADE_BLOCK",
                    details=f"risk={risk_value} reason={risk_check.reason}",
                )
                continue
            raw_equity = payload.get("paper_equity", default_equity)
            try:
                current_equity = float(raw_equity)
            except Exception:
                current_equity = default_equity
            raw_max_dd = payload.get("max_daily_drawdown_pct", config_env.risk.max_daily_drawdown_pct)
            try:
                max_daily_drawdown_pct = float(raw_max_dd)
            except Exception:
                max_daily_drawdown_pct = float(config_env.risk.max_daily_drawdown_pct)
            drawdown_check = drawdown_guard.evaluate(
                user_id=user_id,
                current_equity=current_equity,
                max_daily_drawdown_pct=max_daily_drawdown_pct,
            )
            if not drawdown_check.allowed:
                pause_note = f" reason={drawdown_check.reason}" if drawdown_check.reason.startswith("paused_until_utc_") else ""
                transport.send_text(
                    chat_id=user_id,
                    text=(
                        f"risk_blocked: daily_drawdown={drawdown_check.drawdown_pct:.2f}% "
                        f"limit={drawdown_check.max_drawdown_pct:.2f}%{pause_note}"
                    ),
                )
                risk_alert_notifier.maybe_send(
                    transport=transport,
                    chat_id=user_id,
                    user_id=user_id,
                    code="DAILY_DRAWDOWN_BLOCK",
                    details=(
                        f"daily_drawdown={drawdown_check.drawdown_pct:.2f}% "
                        f"limit={drawdown_check.max_drawdown_pct:.2f}% reason={drawdown_check.reason}"
                    ),
                )
                continue
            raw_max_pos = payload.get("max_open_positions", 1)
            raw_open_pos = payload.get("open_positions_count", 0)
            try:
                max_open_positions = int(raw_max_pos)
            except Exception:
                max_open_positions = 1
            try:
                open_positions_count = int(raw_open_pos)
            except Exception:
                open_positions_count = 0
            if open_positions_count >= max_open_positions:
                transport.send_text(
                    chat_id=user_id,
                    text=f"risk_blocked: open_positions={open_positions_count} limit={max_open_positions}",
                )
                risk_alert_notifier.maybe_send(
                    transport=transport,
                    chat_id=user_id,
                    user_id=user_id,
                    code="MAX_OPEN_POSITIONS_BLOCK",
                    details=f"open_positions={open_positions_count} limit={max_open_positions}",
                )
                continue
            text = (
                f"[{decision.strategy}] {decision.direction} {symbol} {timeframe}\n"
                f"regime={regime.label} confidence={regime.confidence}\n"
                f"ml_prob={ml_probability}\n"
                f"risk_per_trade_pct={risk_check.risk_per_trade_pct}\n"
                f"rr={payload.get('rr_ratio', 2.0)}\n"
                f"open_positions={open_positions_count}/{max_open_positions}\n"
                f"daily_drawdown_pct={drawdown_check.drawdown_pct:.2f}\n"
                f"explain={decision.explain}"
            )
            transport.send_text(chat_id=user_id, text=text)
            if mode == "paper":
                payload["open_positions_count"] = min(max_open_positions, open_positions_count + 1)
                store._cache.set(key, payload)

    pipeline = RealtimeCandlePipeline(symbol=symbol, timeframe=timeframe, on_candle=on_candle)

    async def run_pipeline():
        while True:
            try:
                await pipeline.run()
            except Exception:
                await asyncio.sleep(1)

    await asyncio.gather(_run_runtime(runtime, once=False), run_pipeline())


def _parse_whitelist_symbols(raw: str) -> set[str]:
    items = {part.strip().upper() for part in raw.split(",") if part.strip()}
    return items


def _passes_asset_whitelist(
    symbol: str,
    volume: float,
    high: float,
    low: float,
    close: float,
    allowed_symbols: set[str],
    min_volume: float,
    max_spread_pct: float,
) -> tuple[bool, str]:
    normalized_symbol = symbol.strip().upper()
    if allowed_symbols and normalized_symbol not in allowed_symbols:
        return False, f"symbol_not_allowed:{normalized_symbol}"
    if volume < min_volume:
        return False, f"liquidity_low:volume={volume:.2f}<min={min_volume:.2f}"
    spread_pct = ((high - low) / max(abs(close), 1e-9)) * 100.0
    if spread_pct > max_spread_pct:
        return False, f"spread_high:{spread_pct:.2f}%>max={max_spread_pct:.2f}%"
    return True, "ok"


if __name__ == "__main__":
    main()
