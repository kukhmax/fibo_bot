from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from core.config import load_runtime_secrets
from core.config import validate_runtime_secrets


class TestSecretsLoader(unittest.TestCase):
    def test_load_from_env_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "APP_ENV=paper\n"
                "LOG_LEVEL=DEBUG\n"
                "TELEGRAM_BOT_TOKEN=token_from_file\n"
                "HYPERLIQUID_API_KEY=hl_key\n"
                "HYPERLIQUID_API_SECRET=hl_secret\n",
                encoding="utf-8",
            )

            with patch.dict("os.environ", {}, clear=True):
                secrets = load_runtime_secrets(str(env_path))

            self.assertEqual(secrets.environment, "paper")
            self.assertEqual(secrets.log_level, "DEBUG")
            self.assertEqual(secrets.telegram_bot_token, "token_from_file")
            self.assertEqual(secrets.hyperliquid_api_key, "hl_key")

    def test_os_env_has_priority_over_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "TELEGRAM_BOT_TOKEN=token_from_file\n",
                encoding="utf-8",
            )

            with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "token_from_env"}, clear=True):
                secrets = load_runtime_secrets(str(env_path))

            self.assertEqual(secrets.telegram_bot_token, "token_from_env")

    def test_validate_requires_telegram_token(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            secrets = load_runtime_secrets()
        with self.assertRaises(ValueError):
            validate_runtime_secrets(secrets)

    def test_validate_trading_credentials(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_BOT_TOKEN": "token",
                "HYPERLIQUID_API_KEY": "key",
                "HYPERLIQUID_API_SECRET": "secret",
            },
            clear=True,
        ):
            secrets = load_runtime_secrets()
            validate_runtime_secrets(secrets, require_trading_credentials=True)


if __name__ == "__main__":
    unittest.main()
