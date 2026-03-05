import unittest

from core.bot import CommandContext
from core.bot import CommandRouter
from core.bot import IncomingMessage
from core.bot import TelegramBotRuntime
from core.bot import build_default_router
from core.config import load_environment_config


class _FakeTransport:
    def __init__(self, updates: list[IncomingMessage]) -> None:
        self._updates = list(updates)
        self.sent_messages: list[tuple[int, str]] = []

    def fetch_updates(self, offset: int | None = None, limit: int = 50) -> list[IncomingMessage]:
        if offset is None:
            return self._updates[:limit]
        return [item for item in self._updates if item.update_id >= offset][:limit]

    def send_text(self, chat_id: int, text: str) -> None:
        self.sent_messages.append((chat_id, text))


class TestBotRouter(unittest.IsolatedAsyncioTestCase):
    async def test_command_router_dispatches_registered_command(self) -> None:
        router = CommandRouter()
        router.add_route("/ping", lambda _ctx, _args: "pong")
        result = await router.dispatch(CommandContext(chat_id=1, user_id=2, text="/ping"))
        self.assertTrue(result.handled)
        self.assertEqual(result.response_text, "pong")

    async def test_command_router_handles_unknown_command(self) -> None:
        router = CommandRouter()
        result = await router.dispatch(CommandContext(chat_id=1, user_id=2, text="/missing"))
        self.assertFalse(result.handled)
        self.assertIn("Неизвестная команда", result.response_text)

    async def test_default_router_has_start_and_status(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config)
        start = await router.dispatch(CommandContext(chat_id=1, user_id=2, text="/start"))
        status = await router.dispatch(CommandContext(chat_id=1, user_id=2, text="/status"))
        self.assertTrue(start.handled)
        self.assertTrue(status.handled)
        self.assertIn("fib_bot готов", start.response_text)
        self.assertIn("online", status.response_text)

    async def test_runtime_fetches_updates_and_sends_responses(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config)
        updates = [
            IncomingMessage(update_id=10, chat_id=11, user_id=12, text="/help"),
            IncomingMessage(update_id=11, chat_id=11, user_id=12, text="/unknown"),
        ]
        transport = _FakeTransport(updates)
        runtime = TelegramBotRuntime(router=router, transport=transport)

        processed = await runtime.process_once()

        self.assertEqual(processed, 2)
        self.assertEqual(len(transport.sent_messages), 2)
        self.assertIn("/start", transport.sent_messages[0][1])
        self.assertIn("Неизвестная команда", transport.sent_messages[1][1])


if __name__ == "__main__":
    unittest.main()
