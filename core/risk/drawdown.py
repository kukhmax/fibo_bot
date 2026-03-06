from dataclasses import dataclass
from datetime import datetime
from datetime import timezone

from core.data.persistence import StateCache


@dataclass(frozen=True)
class DailyDrawdownCheck:
    allowed: bool
    drawdown_pct: float
    max_drawdown_pct: float
    reason: str
    start_equity: float
    current_equity: float


class DailyDrawdownGuard:
    def __init__(
        self,
        max_daily_drawdown_pct: float,
        pause_until_utc_hour: int = 0,
        state_cache: StateCache | None = None,
    ) -> None:
        self.max_daily_drawdown_pct = float(max_daily_drawdown_pct)
        self.pause_until_utc_hour = int(pause_until_utc_hour)
        self.state_cache = state_cache or StateCache("runtime/risk_state.json")

    def evaluate(
        self,
        user_id: int,
        current_equity: float,
        max_daily_drawdown_pct: float | None = None,
        now_utc: datetime | None = None,
    ) -> DailyDrawdownCheck:
        limit_pct = self.max_daily_drawdown_pct if max_daily_drawdown_pct is None else float(max_daily_drawdown_pct)
        current_time = now_utc or datetime.now(timezone.utc)
        equity = float(current_equity)
        if equity <= 0:
            return DailyDrawdownCheck(
                allowed=False,
                drawdown_pct=0.0,
                max_drawdown_pct=limit_pct,
                reason="invalid_equity",
                start_equity=equity,
                current_equity=equity,
            )
        day_key = current_time.strftime("%Y-%m-%d")
        state_key = f"daily_drawdown:{user_id}"
        raw_state = self.state_cache.get(state_key, {})
        is_same_day = isinstance(raw_state, dict) and raw_state.get("day_key") == day_key
        if not is_same_day:
            start_equity = equity
        else:
            try:
                start_equity = float(raw_state.get("start_equity", equity))
            except Exception:
                start_equity = equity
        if is_same_day and bool(raw_state.get("paused", False)):
            drawdown_pct = float(raw_state.get("drawdown_pct", 0.0))
            return DailyDrawdownCheck(
                allowed=False,
                drawdown_pct=drawdown_pct,
                max_drawdown_pct=limit_pct,
                reason=f"paused_until_utc_{self.pause_until_utc_hour:02d}",
                start_equity=start_equity,
                current_equity=equity,
            )
        safe_start = max(start_equity, 1e-9)
        drawdown_pct = max(0.0, ((safe_start - equity) / safe_start) * 100.0)
        allowed = drawdown_pct <= limit_pct
        paused = not allowed
        reason = "ok" if allowed else "max_daily_drawdown_exceeded"
        self.state_cache.set(
            state_key,
            {
                "day_key": day_key,
                "start_equity": start_equity,
                "current_equity": equity,
                "drawdown_pct": drawdown_pct,
                "allowed": allowed,
                "paused": paused,
            },
        )
        return DailyDrawdownCheck(
            allowed=allowed,
            drawdown_pct=drawdown_pct,
            max_drawdown_pct=limit_pct,
            reason=reason,
            start_equity=start_equity,
            current_equity=equity,
        )
