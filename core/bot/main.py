from argparse import ArgumentParser
import json
import os
import sys
from time import sleep

from core.bot.health import health_snapshot_dict
from core.config import load_environment_config
from core.config import load_runtime_secrets


def run(once: bool = False) -> None:
    app_env = os.getenv("APP_ENV", "dev")
    config = load_environment_config(app_env)
    secrets = load_runtime_secrets()

    print(
        f"fib_bot app started env={config.environment} mode={config.bot.mode} "
        f"primary_exchange={config.exchange.primary} token_configured={bool(secrets.telegram_bot_token)}"
    )

    if once:
        return

    while True:
        sleep(30)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--health", action="store_true")
    args = parser.parse_args()
    if args.health:
        payload = health_snapshot_dict()
        print(json.dumps(payload, ensure_ascii=False))
        sys.exit(0 if payload["healthy"] else 1)
    run(once=args.once)


if __name__ == "__main__":
    main()
