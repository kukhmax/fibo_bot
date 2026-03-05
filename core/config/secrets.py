from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class RuntimeSecrets:
    telegram_bot_token: str
    hyperliquid_api_key: str
    hyperliquid_api_secret: str
    mexc_api_key: str
    mexc_api_secret: str
    environment: str
    log_level: str


def load_runtime_secrets(env_file_path: str | None = None) -> RuntimeSecrets:
    file_values = _load_env_file(env_file_path) if env_file_path else {}

    def resolve(key: str, default: str = "") -> str:
        raw_value = os.getenv(key, file_values.get(key, default))
        return str(raw_value).strip()

    return RuntimeSecrets(
        telegram_bot_token=resolve("TELEGRAM_BOT_TOKEN"),
        hyperliquid_api_key=resolve("HYPERLIQUID_API_KEY"),
        hyperliquid_api_secret=resolve("HYPERLIQUID_API_SECRET"),
        mexc_api_key=resolve("MEXC_API_KEY"),
        mexc_api_secret=resolve("MEXC_API_SECRET"),
        environment=resolve("APP_ENV", "dev"),
        log_level=resolve("LOG_LEVEL", "INFO"),
    )


def validate_runtime_secrets(
    secrets: RuntimeSecrets, require_trading_credentials: bool = False
) -> None:
    if not secrets.telegram_bot_token:
        raise ValueError("Missing required secret: TELEGRAM_BOT_TOKEN")

    if require_trading_credentials:
        if not secrets.hyperliquid_api_key or not secrets.hyperliquid_api_secret:
            raise ValueError(
                "Missing required trading secrets: HYPERLIQUID_API_KEY/HYPERLIQUID_API_SECRET"
            )


def _load_env_file(env_file_path: str) -> dict[str, str]:
    path = Path(env_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Env file not found: {env_file_path}")

    result: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as env_file:
        for line in env_file:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
                continue
            key, value = stripped_line.split("=", 1)
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result
