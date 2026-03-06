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
    inline_keyboard: tuple[tuple[tuple[str, str], ...], ...] | None = None


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
        if isinstance(result, dict) and "text" in result:
            text = str(result.get("text", ""))
            inline = result.get("inline_keyboard")
            reply = result.get("reply_keyboard")
            rk = self._reply_keyboard if reply is None else reply
            return RouteResult(handled=True, response_text=text, reply_keyboard=rk, inline_keyboard=inline)
        return self._result(handled=True, response_text=result)

    def available_commands(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def _parse_command(self, text: str) -> tuple[str | None, str]:
        stripped = text.strip()
        if not stripped.startswith("/"):
            quick_map = {
                "📊 Статус": "/status",
                "📍 Позиции": "/positions",
                "🧩 Пары": "/pairs",
                "⏱ Таймфрейм": "/tf_menu",
                "🛡 Риск": "/risk",
                "🤖 Режим": "/mode_menu",
                "🧪 Backtest": "/backtest",
                "🧠 ML отчет": "/ml_report",
                "📰 News": "/news",
                "🧭 Readiness": "/readiness",
                "🙈 Скрыть меню": "/hide_menu",
                "🏠 Меню": "/menu",
                "➕ Добавить пару": "/pair_add",
                "➖ Удалить пару": "/pair_remove",
                "⚡ TF 1m": "/set_tf 1m",
                "🚀 TF 5m": "/set_tf 5m",
                "📘 TF 15m": "/set_tf 15m",
                "🕐 TF 1h": "/set_tf 1h",
                "🌙 TF 4h": "/set_tf 4h",
                "🛡 Risk 0.5%": "/set_risk 0.5",
                "🛡 Risk 1.0%": "/set_risk 1.0",
                "🛡 Risk 1.5%": "/set_risk 1.5",
                "🎯 RR 1.5": "/set_rr 1.5",
                "🎯 RR 2.0": "/set_rr 2.0",
                "🎯 RR 2.5": "/set_rr 2.5",
                "🚫 DD 5%": "/set_dd 5",
                "🚫 DD 8%": "/set_dd 8",
                "🚫 DD 10%": "/set_dd 10",
                "📦 MaxPos 1": "/set_maxpos 1",
                "📦 MaxPos 2": "/set_maxpos 2",
                "📦 MaxPos 3": "/set_maxpos 3",
                "🧯 SL 0.5%": "/set_sl 0.5",
                "🧯 SL 1.0%": "/set_sl 1.0",
                "💰 TP 1.0%": "/set_tp 1.0",
                "💰 TP 2.0%": "/set_tp 2.0",
            }
            mapped = quick_map.get(_normalize_menu_text(stripped))
            if mapped is None:
                return "/text", stripped
            stripped = mapped
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
            inline_keyboard=None,
        )


def _normalize_menu_text(value: str) -> str:
    return value.replace("\ufe0f", "").strip()
