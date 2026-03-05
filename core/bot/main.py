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
    asyncio.run(_run_runtime(runtime=runtime, once=once))


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
