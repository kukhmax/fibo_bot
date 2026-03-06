import tempfile
import unittest
from pathlib import Path

from core.bot import IncomingMessage
from core.bot import TelegramBotRuntime
from core.bot import TelegramUserProfileStore
from core.bot import build_default_router
from core.config import load_environment_config
from core.data import StateCache


class _FlowTransport:
    def __init__(self, updates: list[IncomingMessage]) -> None:
        self._updates = list(updates)
        self.sent_messages: list[
            tuple[
                int,
                str,
                tuple[tuple[str, ...], ...] | None,
                tuple[tuple[tuple[str, str], ...], ...] | None,
            ]
        ] = []

    def fetch_updates(self, offset: int | None = None, limit: int = 50) -> list[IncomingMessage]:
        if offset is None:
            return self._updates[:limit]
        return [item for item in self._updates if item.update_id >= offset][:limit]

    def send_text(
        self,
        chat_id: int,
        text: str,
        reply_keyboard: tuple[tuple[str, ...], ...] | None = None,
        inline_keyboard: tuple[tuple[tuple[str, str], ...], ...] | None = None,
    ) -> None:
        self.sent_messages.append((chat_id, text, reply_keyboard, inline_keyboard))


class TestIntegrationUserFlows(unittest.IsolatedAsyncioTestCase):
    async def test_onboarding_flow_updates_timeframe_via_inline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = TelegramUserProfileStore(cache=StateCache(Path(tmp) / "profiles.json"))
            config = load_environment_config("dev")
            router = build_default_router(config, profile_store=store)
            updates = [
                IncomingMessage(update_id=1, chat_id=100, user_id=42, text="/start"),
                IncomingMessage(update_id=2, chat_id=100, user_id=42, text="/menu"),
                IncomingMessage(update_id=3, chat_id=100, user_id=42, text="/tf_menu"),
                IncomingMessage(update_id=4, chat_id=100, user_id=42, text="/set_tf 1h"),
                IncomingMessage(update_id=5, chat_id=100, user_id=42, text="/status"),
            ]
            transport = _FlowTransport(updates=updates)
            runtime = TelegramBotRuntime(router=router, transport=transport)

            processed = await runtime.process_once()

            self.assertEqual(processed, 5)
            self.assertEqual(len(transport.sent_messages), 5)
            self.assertIn("Добро пожаловать", transport.sent_messages[0][1])
            self.assertEqual(transport.sent_messages[0][2], ())
            self.assertIn("Выбор таймфрейма", transport.sent_messages[2][1])
            self.assertIn("Таймфрейм обновлен: 1h", transport.sent_messages[3][1])
            self.assertIn("Таймфрейм: 1h", transport.sent_messages[4][1])

    async def test_risk_and_mode_flow_applies_preset_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = TelegramUserProfileStore(cache=StateCache(Path(tmp) / "profiles.json"))
            config = load_environment_config("dev")
            router = build_default_router(config, profile_store=store)
            updates = [
                IncomingMessage(update_id=11, chat_id=101, user_id=77, text="/mode_menu"),
                IncomingMessage(update_id=12, chat_id=101, user_id=77, text="/mode paper"),
                IncomingMessage(update_id=13, chat_id=101, user_id=77, text="/risk"),
                IncomingMessage(update_id=14, chat_id=101, user_id=77, text="/set_risk 1.0"),
                IncomingMessage(update_id=15, chat_id=101, user_id=77, text="/set_rr 2.5"),
                IncomingMessage(update_id=16, chat_id=101, user_id=77, text="/status"),
            ]
            transport = _FlowTransport(updates=updates)
            runtime = TelegramBotRuntime(router=router, transport=transport)

            processed = await runtime.process_once()

            self.assertEqual(processed, 6)
            self.assertIn("Выбор режима", transport.sent_messages[0][1])
            self.assertIn("Режим обновлен: paper", transport.sent_messages[1][1])
            self.assertIn("Меню риска", transport.sent_messages[2][1])
            self.assertIn("Риск на сделку обновлен: 1.0%", transport.sent_messages[3][1])
            self.assertIn("Risk/Reward обновлен: 2.5", transport.sent_messages[4][1])
            self.assertIn("Режим: paper", transport.sent_messages[5][1])
            self.assertIn("Риск: 1.0%", transport.sent_messages[5][1])
            self.assertIn("RR: 2.5", transport.sent_messages[5][1])


if __name__ == "__main__":
    unittest.main()
