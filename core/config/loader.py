import json
from pathlib import Path

from core.config.models import BotConfig
from core.config.models import EnvironmentConfig
from core.config.models import ExchangeConfig
from core.config.models import MLConfig
from core.config.models import RiskConfig
from core.risk import RiskManager


CONFIG_DIR = Path(__file__).resolve().parent / "profiles"
ALLOWED_ENVIRONMENTS = {"dev", "test", "paper"}
RISK_MANAGER = RiskManager()


def load_environment_config(environment: str) -> EnvironmentConfig:
    normalized_environment = environment.strip().lower()
    if normalized_environment not in ALLOWED_ENVIRONMENTS:
        raise ValueError(f"Unsupported environment: {environment}")

    config_path = CONFIG_DIR / f"{normalized_environment}.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as config_file:
        payload = json.load(config_file)
    risk_payload = payload["risk"]
    risk_check = RISK_MANAGER.validate_risk_per_trade_pct(float(risk_payload["risk_per_trade_pct"]))
    if not risk_check.allowed:
        raise ValueError(f"Invalid risk_per_trade_pct in {config_path.name}: {risk_check.reason}")
    max_daily_drawdown_pct = float(risk_payload["max_daily_drawdown_pct"])
    if max_daily_drawdown_pct <= 0 or max_daily_drawdown_pct > 10:
        raise ValueError(f"Invalid max_daily_drawdown_pct in {config_path.name}: must be in range 0..10")

    return EnvironmentConfig(
        environment=payload["environment"],
        exchange=ExchangeConfig(**payload["exchange"]),
        bot=BotConfig(**payload["bot"]),
        risk=RiskConfig(**payload["risk"]),
        ml=MLConfig(**payload["ml"]),
    )
