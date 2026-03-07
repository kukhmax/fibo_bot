from dataclasses import dataclass
import os
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
    callback_query_id: str | None = None


class TelegramTransportProtocol(Protocol):
    def fetch_updates(self, offset: int | None = None, limit: int = 50) -> list[IncomingMessage]:
        ...

    def send_text(
        self,
        chat_id: int,
        text: str,
        reply_keyboard: tuple[tuple[str, ...], ...] | None = None,
        inline_keyboard: tuple[tuple[tuple[str, str], ...], ...] | None = None,
    ) -> None:
        ...

    def answer_callback_query(self, callback_query_id: str) -> None:
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
        self._event_logs_enabled = bool(int(os.getenv("BOT_EVENT_LOGS", "1")))

    async def process_once(self) -> int:
        updates = self.transport.fetch_updates(offset=self._offset)
        if not updates:
            self._maybe_send_scheduled_reports()
            return 0
        for update in updates:
            self._offset = update.update_id + 1
            self._log_event(
                f"incoming update_id={update.update_id} chat_id={update.chat_id} user_id={update.user_id} text={_short(update.text)}"
            )
            context = CommandContext(
                chat_id=update.chat_id,
                user_id=update.user_id,
                text=update.text,
            )
            result = await self.router.dispatch(context)
            if update.callback_query_id:
                try:
                    self.transport.answer_callback_query(update.callback_query_id)
                except Exception as e:
                    self._log_event(f"answer_callback_query_failed id={update.callback_query_id} error={e}")
            self._log_event(
                f"result handled={result.handled} reply_kb={'yes' if result.reply_keyboard is not None else 'no'} "
                f"inline_kb={'yes' if result.inline_keyboard is not None else 'no'} text={_short(result.response_text)}"
            )
            self.transport.send_text(
                update.chat_id,
                result.response_text,
                reply_keyboard=result.reply_keyboard,
                inline_keyboard=result.inline_keyboard,
            )
        self._maybe_send_scheduled_reports()
        return len(updates)

    def _maybe_send_scheduled_reports(self) -> None:
        if self._profiles is None:
            return
        if not bool(int(os.getenv("AUTO_POSITION_REPORTS", "0"))):
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
            if last_sent == 0:
                self._report_state.set(f"last:{user_id}", now)
                continue
            due = (now - last_sent) >= interval_min * 60
            if not due:
                continue
            profile = self._profiles.get(user_id)
            if profile is None:
                continue
            report_text = self._reporter.build_report(profile)
            self.transport.send_text(chat_id=user_id, text=report_text)
            self._report_state.set(f"last:{user_id}", now)
            self._log_event(f"scheduled_report_sent user_id={user_id} interval_min={interval_min}")

    def _log_event(self, message: str) -> None:
        if not self._event_logs_enabled:
            return
        print(f"bot_runtime: {message}")


def _short(text: str, limit: int = 140) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."
