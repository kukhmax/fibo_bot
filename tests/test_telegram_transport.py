import json
import unittest
from unittest.mock import patch

from core.bot import TelegramApiTransport


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestTelegramTransport(unittest.TestCase):
    def test_fetch_updates_parses_text_messages(self) -> None:
        transport = TelegramApiTransport(bot_token="token123", poll_timeout_seconds=5)

        def fake_urlopen(req, timeout=30):
            self.assertIn("/getUpdates", req.full_url)
            self.assertIn("offset=11", req.full_url)
            self.assertIn("limit=50", req.full_url)
            return _FakeResponse(
                {
                    "ok": True,
                    "result": [
                        {
                            "update_id": 11,
                            "message": {
                                "chat": {"id": 1001},
                                "from": {"id": 2002},
                                "text": "/status",
                            },
                        },
                        {
                            "update_id": 12,
                            "message": {
                                "chat": {"id": 1001},
                                "from": {"id": 2002},
                            },
                        },
                    ],
                }
            )

        with patch("core.bot.telegram_transport.request.urlopen", side_effect=fake_urlopen):
            updates = transport.fetch_updates(offset=11, limit=50)
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0].update_id, 11)
        self.assertEqual(updates[0].chat_id, 1001)
        self.assertEqual(updates[0].user_id, 2002)
        self.assertEqual(updates[0].text, "/status")

    def test_send_text_includes_reply_markup(self) -> None:
        transport = TelegramApiTransport(bot_token="token123")
        captured: dict[str, object] = {}

        def fake_urlopen(req, timeout=30):
            captured["url"] = req.full_url
            captured["method"] = req.get_method()
            captured["payload"] = json.loads((req.data or b"{}").decode("utf-8"))
            return _FakeResponse({"ok": True, "result": {"message_id": 1}})

        keyboard = (("/start", "/status"), ("/mode paper",))
        with patch("core.bot.telegram_transport.request.urlopen", side_effect=fake_urlopen):
            transport.send_text(chat_id=7, text="ok", reply_keyboard=keyboard)

        self.assertIn("/sendMessage", captured["url"])
        self.assertEqual(captured["method"], "POST")
        payload = captured["payload"]
        self.assertEqual(payload["chat_id"], 7)
        self.assertEqual(payload["text"], "ok")
        self.assertIn("reply_markup", payload)
        self.assertTrue(payload["reply_markup"]["resize_keyboard"])


if __name__ == "__main__":
    unittest.main()
