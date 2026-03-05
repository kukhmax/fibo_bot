import unittest
from unittest.mock import patch

from core.bot.health import health_snapshot_dict


class TestHealthSnapshot(unittest.TestCase):
    @patch("core.bot.health._check_tcp_dependency")
    def test_health_snapshot_healthy(self, check_tcp) -> None:
        check_tcp.return_value = True
        with patch.dict(
            "os.environ",
            {
                "APP_ENV": "dev",
                "REDIS_URL": "redis://127.0.0.1:6379/0",
                "DATABASE_URL": "postgresql://user:pass@127.0.0.1:5432/db",
                "TELEGRAM_BOT_TOKEN": "token",
            },
            clear=True,
        ):
            payload = health_snapshot_dict()

        self.assertEqual(payload["app"], "fib_bot")
        self.assertEqual(payload["environment"], "dev")
        self.assertTrue(payload["healthy"])
        self.assertTrue(payload["telegram_token_configured"])
        self.assertEqual(len(payload["dependencies"]), 2)
        self.assertEqual(payload["dependencies"][0]["name"], "redis")
        self.assertEqual(payload["dependencies"][1]["name"], "postgres")

    @patch("core.bot.health._check_tcp_dependency")
    def test_health_snapshot_degraded(self, check_tcp) -> None:
        check_tcp.side_effect = [True, False]
        with patch.dict("os.environ", {"APP_ENV": "test"}, clear=True):
            payload = health_snapshot_dict()

        self.assertFalse(payload["healthy"])
        self.assertFalse(payload["dependencies"][1]["healthy"])


if __name__ == "__main__":
    unittest.main()
