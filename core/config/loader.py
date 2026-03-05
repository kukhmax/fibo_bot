import json
from pathlib import Path

from core.config.models import BotConfig
from core.config.models import EnvironmentConfig
from core.config.models import ExchangeConfig
from core.config.models import MLConfig
from core.config.models import RiskConfig


CONFIG_DIR = Path(__file__).resolve().parent / "profiles"
ALLOWED_ENVIRONMENTS = {"dev", "test", "paper"}


def load_environment_config(environment: str) -> EnvironmentConfig:
    normalized_environment = environment.strip().lower()
    if normalized_environment not in ALLOWED_ENVIRONMENTS:
        raise ValueError(f"Unsupported environment: {environment}")

    config_path = CONFIG_DIR / f"{normalized_environment}.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as config_file:
        payload = json.load(config_file)

    return EnvironmentConfig(
        environment=payload["environment"],
        exchange=ExchangeConfig(**payload["exchange"]),
        bot=BotConfig(**payload["bot"]),
        risk=RiskConfig(**payload["risk"]),
        ml=MLConfig(**payload["ml"]),
    )
