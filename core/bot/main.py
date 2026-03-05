from argparse import ArgumentParser
import asyncio
from collections import deque
import json
import os
import sys

from core.bot.commands import build_default_router
from core.bot.health import health_snapshot_dict
from core.bot.profile import TelegramUserProfileStore
from core.bot.runtime import TelegramBotRuntime
from core.bot.telegram_transport import TelegramApiTransport
from core.data.pipeline import RealtimeCandlePipeline
from core.regime import RuleBasedRegimeClassifier
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


if __name__ == "__main__":
    main()


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

    async def on_candle(candle):
        regime_window.append(candle)
        regime = classifier.classify(list(regime_window))
        if strategy_mode in strategies:
            strategy_name = strategy_mode
        else:
            strategy_name = select_strategy_by_regime(regime.label, fallback="trend_pullback")
        decision = strategies[strategy_name].on_candle(candle)
        if decision.action != "entry":
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
            text = (
                f"[{decision.strategy}] {decision.direction} {symbol} {timeframe}\n"
                f"regime={regime.label} confidence={regime.confidence}\n"
                f"explain={decision.explain}"
            )
            transport.send_text(chat_id=user_id, text=text)

    pipeline = RealtimeCandlePipeline(symbol=symbol, timeframe=timeframe, on_candle=on_candle)

    async def run_pipeline():
        while True:
            try:
                await pipeline.run()
            except Exception:
                await asyncio.sleep(1)

    await asyncio.gather(_run_runtime(runtime, once=False), run_pipeline())
