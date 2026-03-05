from dataclasses import dataclass
import inspect
from typing import Awaitable
from typing import Callable


@dataclass(frozen=True)
class CommandContext:
    chat_id: int
    user_id: int
    text: str


@dataclass(frozen=True)
class RouteResult:
    handled: bool
    response_text: str
    reply_keyboard: tuple[tuple[str, ...], ...] | None = None


CommandHandler = Callable[[CommandContext, str], str | Awaitable[str]]


class CommandRouter:
    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler] = {}
        self._reply_keyboard: tuple[tuple[str, ...], ...] | None = None

    def add_route(self, command: str, handler: CommandHandler) -> None:
        normalized = self._normalize(command)
        self._handlers[normalized] = handler

    def set_reply_keyboard(self, rows: list[list[str]] | tuple[tuple[str, ...], ...]) -> None:
        normalized: list[tuple[str, ...]] = []
        for row in rows:
            cleaned = tuple(item.strip() for item in row if item.strip())
            if cleaned:
                normalized.append(cleaned)
        self._reply_keyboard = tuple(normalized) if normalized else None

    async def dispatch(self, context: CommandContext) -> RouteResult:
        command, args = self._parse_command(context.text)
        if command is None:
            return self._result(handled=False, response_text="Команда не распознана.")
        handler = self._handlers.get(command)
        if handler is None:
            return self._result(handled=False, response_text=f"Неизвестная команда: {command}")
        result = handler(context, args)
        if inspect.isawaitable(result):
            result = await result
        return self._result(handled=True, response_text=result)

    def available_commands(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def _parse_command(self, text: str) -> tuple[str | None, str]:
        stripped = text.strip()
        if not stripped.startswith("/"):
            return None, ""
        parts = stripped.split(maxsplit=1)
        command = self._normalize(parts[0].split("@", 1)[0])
        args = parts[1] if len(parts) > 1 else ""
        return command, args

    def _normalize(self, command: str) -> str:
        normalized = command.strip().lower()
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        return normalized

    def _result(self, handled: bool, response_text: str) -> RouteResult:
        return RouteResult(
            handled=handled,
            response_text=response_text,
            reply_keyboard=self._reply_keyboard,
        )
