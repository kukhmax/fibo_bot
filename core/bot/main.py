from argparse import ArgumentParser
import asyncio
import json
import os
import sys

from core.bot.commands import build_default_router
from core.bot.health import health_snapshot_dict
from core.bot.runtime import TelegramBotRuntime
from core.bot.telegram_transport import TelegramApiTransport
from core.bot.profile import TelegramUserProfileStore
from core.data.pipeline import RealtimeCandlePipeline
from core.strategies import TrendPullbackStrategy, VolatilityBreakoutStrategy, LiquiditySweepReversalStrategy
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
    runtime = TelegramBotRuntime(
        router=router,
        transport=TelegramApiTransport(bot_token=secrets.telegram_bot_token),
        profile_store=store,
    )
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
    strategy_name = os.getenv("FIB_STRATEGY", "trend_pullback").strip().lower()
    if strategy_name == "volatility_breakout":
        strategy = VolatilityBreakoutStrategy()
    elif strategy_name == "liquidity_sweep":
        strategy = LiquiditySweepReversalStrategy()
    else:
        strategy = TrendPullbackStrategy()

    async def on_candle(candle):
        signal = strategy.on_candle(candle)
        if signal is None:
            return
        # Broadcast to users in signal_only/paper
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
                f"[Trend Pullback] {signal.direction} {symbol} {timeframe}\n"
                f"reason={signal.reason}"
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
