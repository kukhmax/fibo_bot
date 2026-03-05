from dataclasses import asdict
from dataclasses import dataclass

from core.config.models import EnvironmentConfig
from core.data.persistence import StateCache


@dataclass(frozen=True)
class TelegramUserProfile:
    user_id: int
    mode: str
    exchange: str
    timeframe: str
    risk_per_trade_pct: float
    position_report_minutes: int


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
            exchange=config.exchange.primary,
            timeframe=config.exchange.default_timeframe,
            risk_per_trade_pct=config.risk.risk_per_trade_pct,
            position_report_minutes=config.bot.position_report_minutes,
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
            exchange=str(payload["exchange"]),
            timeframe=str(payload["timeframe"]),
            risk_per_trade_pct=float(payload["risk_per_trade_pct"]),
            position_report_minutes=int(payload["position_report_minutes"]),
        )

    def save(self, profile: TelegramUserProfile) -> None:
        self._cache.set(self._key(profile.user_id), asdict(profile))

    def _key(self, user_id: int) -> str:
        return f"profile:{user_id}"
