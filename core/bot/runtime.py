from dataclasses import dataclass
from typing import Protocol
import time

from core.bot.router import CommandContext
from core.bot.router import CommandRouter
from core.bot.profile import TelegramUserProfileStore
from core.bot.reporter import PositionReporter
from core.data.persistence import StateCache


@dataclass(frozen=True)
class IncomingMessage:
    update_id: int
    chat_id: int
    user_id: int
    text: str


class TelegramTransportProtocol(Protocol):
    def fetch_updates(self, offset: int | None = None, limit: int = 50) -> list[IncomingMessage]:
        ...

    def send_text(
        self,
        chat_id: int,
        text: str,
        reply_keyboard: tuple[tuple[str, ...], ...] | None = None,
    ) -> None:
        ...


class TelegramBotRuntime:
    def __init__(
        self,
        router: CommandRouter,
        transport: TelegramTransportProtocol,
        profile_store: TelegramUserProfileStore | None = None,
        reporter: PositionReporter | None = None,
        report_state: StateCache | None = None,
    ) -> None:
        self.router = router
        self.transport = transport
        self._offset: int | None = None
        self._profiles = profile_store
        self._reporter = reporter or PositionReporter()
        self._report_state = report_state or StateCache("runtime/report_last_sent.json")

    async def process_once(self) -> int:
        updates = self.transport.fetch_updates(offset=self._offset)
        if not updates:
            self._maybe_send_scheduled_reports()
            return 0
        for update in updates:
            self._offset = update.update_id + 1
            context = CommandContext(
                chat_id=update.chat_id,
                user_id=update.user_id,
                text=update.text,
            )
            result = await self.router.dispatch(context)
            self.transport.send_text(
                update.chat_id,
                result.response_text,
                reply_keyboard=result.reply_keyboard,
            )
        self._maybe_send_scheduled_reports()
        return len(updates)

    def _maybe_send_scheduled_reports(self) -> None:
        if self._profiles is None:
            return
        state = self._profiles._cache.load()
        now = int(time.time())
        for key, payload in state.items():
            if not isinstance(key, str) or not key.startswith("profile:"):
                continue
            try:
                user_id = int(key.split(":", 1)[1])
            except Exception:
                continue
            try:
                interval_min = int(payload.get("position_report_minutes", 60))
            except Exception:
                interval_min = 60
            if interval_min <= 0:
                continue
            last_sent = int(self._report_state.get(f"last:{user_id}", 0) or 0)
            due = last_sent == 0 or (now - last_sent) >= interval_min * 60
            if not due:
                continue
            profile = self._profiles.get(user_id)
            if profile is None:
                continue
            report_text = self._reporter.build_report(profile)
            self.transport.send_text(chat_id=user_id, text=report_text)
            self._report_state.set(f"last:{user_id}", now)
