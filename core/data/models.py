from dataclasses import dataclass


@dataclass(frozen=True)
class Tick:
    symbol: str
    timestamp_ms: int
    price: float
    volume: float


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    open_time_ms: int
    close_time_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class DataQualityReport:
    symbol: str
    timeframe: str
    is_valid: bool
    issues: tuple[str, ...]
