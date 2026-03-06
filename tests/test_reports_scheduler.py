import tempfile
import unittest
from pathlib import Path
import time
from unittest.mock import patch

from core.bot import CommandRouter, TelegramBotRuntime, IncomingMessage, build_default_router, TelegramUserProfileStore
from core.config import load_environment_config
from core.data import StateCache


class _EmptyTransport:
    def __init__(self) -> None:
        self.sent_messages: list[tuple[int, str]] = []

    def fetch_updates(self, offset=None, limit: int = 50):
        return []

    def send_text(self, chat_id: int, text: str, reply_keyboard=None) -> None:
        self.sent_messages.append((chat_id, text))


class TestReportsScheduler(unittest.IsolatedAsyncioTestCase):
    async def test_sends_report_when_due(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Setup store and create profile with small interval
            store = TelegramUserProfileStore(cache=StateCache(Path(tmp) / "profiles.json"))
            config = load_environment_config("dev")
            profile = store.get_or_create(777, config)
            store.save(type(profile)(**{**profile.__dict__, "position_report_minutes": 1}))

            # Ensure last_sent is old enough
            report_state = StateCache(Path(tmp) / "report_state.json")
            past = int(time.time()) - 3600
            report_state.set("last:777", past)

            transport = _EmptyTransport()
            router = build_default_router(config, profile_store=store)
            runtime = TelegramBotRuntime(router=router, transport=transport, profile_store=store, report_state=report_state)

            with patch.dict("os.environ", {"AUTO_POSITION_REPORTS": "1"}, clear=False):
                processed = await runtime.process_once()
            self.assertEqual(processed, 0)
            self.assertTrue(any(chat_id == 777 for (chat_id, _text) in transport.sent_messages))


if __name__ == "__main__":
    unittest.main()
