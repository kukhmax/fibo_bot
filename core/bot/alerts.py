from datetime import datetime
from datetime import timezone

from core.data.persistence import StateCache


class RiskAlertNotifier:
    def __init__(self, cooldown_minutes: int = 30, state_cache: StateCache | None = None) -> None:
        self.cooldown_minutes = int(cooldown_minutes)
        self.state_cache = state_cache or StateCache("runtime/risk_alert_state.json")

    def maybe_send(
        self,
        transport,
        chat_id: int,
        user_id: int,
        code: str,
        details: str,
        now_utc: datetime | None = None,
    ) -> bool:
        current_time = now_utc or datetime.now(timezone.utc)
        state_key = f"risk_alert:{user_id}:{code}"
        raw_state = self.state_cache.get(state_key, {})
        if isinstance(raw_state, dict):
            try:
                last_sent_epoch = int(raw_state.get("last_sent_epoch", 0))
            except Exception:
                last_sent_epoch = 0
        else:
            last_sent_epoch = 0
        current_epoch = int(current_time.timestamp())
        cooldown_seconds = max(0, self.cooldown_minutes * 60)
        if last_sent_epoch > 0 and (current_epoch - last_sent_epoch) < cooldown_seconds:
            return False
        message = (
            "🚨 КРИТИЧЕСКИЙ РИСК-АЛЕРТ\n"
            f"code={code}\n"
            f"{details}\n"
            f"ts={current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        transport.send_text(chat_id=chat_id, text=message)
        self.state_cache.set(
            state_key,
            {
                "last_sent_epoch": current_epoch,
                "code": code,
                "details": details,
            },
        )
        return True
