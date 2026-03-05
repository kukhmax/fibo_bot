from dataclasses import dataclass
from typing import Protocol

from core.bot.router import CommandContext
from core.bot.router import CommandRouter


@dataclass(frozen=True)
class IncomingMessage:
    update_id: int
    chat_id: int
    user_id: int
    text: str


class TelegramTransportProtocol(Protocol):
    def fetch_updates(self, offset: int | None = None, limit: int = 50) -> list[IncomingMessage]:
        ...

    def send_text(self, chat_id: int, text: str) -> None:
        ...


class TelegramBotRuntime:
    def __init__(self, router: CommandRouter, transport: TelegramTransportProtocol) -> None:
        self.router = router
        self.transport = transport
        self._offset: int | None = None

    async def process_once(self) -> int:
        updates = self.transport.fetch_updates(offset=self._offset)
        if not updates:
            return 0
        for update in updates:
            self._offset = update.update_id + 1
            context = CommandContext(
                chat_id=update.chat_id,
                user_id=update.user_id,
                text=update.text,
            )
            result = await self.router.dispatch(context)
            self.transport.send_text(update.chat_id, result.response_text)
        return len(updates)
