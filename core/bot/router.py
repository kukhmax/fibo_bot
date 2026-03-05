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


CommandHandler = Callable[[CommandContext, str], str | Awaitable[str]]


class CommandRouter:
    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler] = {}

    def add_route(self, command: str, handler: CommandHandler) -> None:
        normalized = self._normalize(command)
        self._handlers[normalized] = handler

    async def dispatch(self, context: CommandContext) -> RouteResult:
        command, args = self._parse_command(context.text)
        if command is None:
            return RouteResult(handled=False, response_text="Команда не распознана.")
        handler = self._handlers.get(command)
        if handler is None:
            return RouteResult(handled=False, response_text=f"Неизвестная команда: {command}")
        result = handler(context, args)
        if inspect.isawaitable(result):
            result = await result
        return RouteResult(handled=True, response_text=result)

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
