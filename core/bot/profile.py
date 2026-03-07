from dataclasses import asdict
from dataclasses import dataclass

from core.config.models import EnvironmentConfig
from core.data.persistence import StateCache


@dataclass(frozen=True)
class TradingPairSettings:
    symbol: str
    timeframe: str


@dataclass(frozen=True)
class TelegramUserProfile:
    user_id: int
    mode: str
    is_running: bool
    exchange: str
    timeframe: str
    risk_per_trade_pct: float
    rr_ratio: float
    max_daily_drawdown_pct: float
    max_open_positions: int
    sl_pct: float
    tp_pct: float
    open_positions_count: int
    position_report_minutes: int
    trading_pairs: tuple[TradingPairSettings, ...]


class TelegramUserProfileStore:
    def __init__(self, cache: StateCache | None = None) -> None:
        self._cache = cache or StateCache("runtime/telegram_profiles.json")

    def get_or_create(self, user_id: int, config: EnvironmentConfig) -> TelegramUserProfile:
        existing = self.get(user_id)
        if existing is not None:
            return existing
        created = TelegramUserProfile(
            user_id=user_id,
            mode=config.bot.mode,
            is_running=False,  # Stopped by default
            exchange=config.exchange.primary,
            timeframe=config.exchange.default_timeframe,
            risk_per_trade_pct=config.risk.risk_per_trade_pct,
            rr_ratio=2.0,
            max_daily_drawdown_pct=config.risk.max_daily_drawdown_pct,
            max_open_positions=1,
            sl_pct=0.5,
            tp_pct=1.0,
            open_positions_count=0,
            position_report_minutes=config.bot.position_report_minutes,
            trading_pairs=(TradingPairSettings(symbol="BTCUSDT", timeframe=config.exchange.default_timeframe),),
        )
        self.save(created)
        return created

    def get(self, user_id: int) -> TelegramUserProfile | None:
        payload = self._cache.get(self._key(user_id))
        if not isinstance(payload, dict):
            return None
        return TelegramUserProfile(
            user_id=int(payload["user_id"]),
            mode=str(payload["mode"]),
            is_running=bool(payload.get("is_running", False)),
            exchange=str(payload["exchange"]),
            timeframe=str(payload["timeframe"]),
            risk_per_trade_pct=float(payload["risk_per_trade_pct"]),
            rr_ratio=float(payload.get("rr_ratio", 2.0)),
            max_daily_drawdown_pct=float(payload.get("max_daily_drawdown_pct", 10.0)),
            max_open_positions=int(payload.get("max_open_positions", 1)),
            sl_pct=float(payload.get("sl_pct", 0.5)),
            tp_pct=float(payload.get("tp_pct", 1.0)),
            open_positions_count=int(payload.get("open_positions_count", 0)),
            position_report_minutes=int(payload["position_report_minutes"]),
            trading_pairs=_parse_trading_pairs(payload.get("trading_pairs"), fallback_timeframe=str(payload["timeframe"])),
        )

    def save(self, profile: TelegramUserProfile) -> None:
        self._cache.set(self._key(profile.user_id), asdict(profile))

    def _key(self, user_id: int) -> str:
        return f"profile:{user_id}"


def _parse_trading_pairs(raw: object, fallback_timeframe: str) -> tuple[TradingPairSettings, ...]:
    if not isinstance(raw, list):
        return (TradingPairSettings(symbol="BTCUSDT", timeframe=fallback_timeframe),)
    pairs: list[TradingPairSettings] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol", "")).strip().upper()
        timeframe = str(item.get("timeframe", "")).strip().lower()
        if not symbol or not timeframe:
            continue
        pairs.append(TradingPairSettings(symbol=symbol, timeframe=timeframe))
    if not pairs:
        return (TradingPairSettings(symbol="BTCUSDT", timeframe=fallback_timeframe),)
    unique: dict[str, TradingPairSettings] = {}
    for pair in pairs:
        unique[pair.symbol] = pair
    return tuple(unique.values())
