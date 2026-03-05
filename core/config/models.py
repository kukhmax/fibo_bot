from dataclasses import dataclass


@dataclass(frozen=True)
class ExchangeConfig:
    primary: str
    backup: str
    default_timeframe: str


@dataclass(frozen=True)
class BotConfig:
    mode: str
    access_mode: str
    position_report_minutes: int


@dataclass(frozen=True)
class RiskConfig:
    risk_per_trade_pct: float
    max_daily_drawdown_pct: float
    pause_until_utc_hour: int


@dataclass(frozen=True)
class MLConfig:
    enabled: bool
    historical_analysis_enabled: bool


@dataclass(frozen=True)
class EnvironmentConfig:
    environment: str
    exchange: ExchangeConfig
    bot: BotConfig
    risk: RiskConfig
    ml: MLConfig
