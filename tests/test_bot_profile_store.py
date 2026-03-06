from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from core.bot import TelegramUserProfileStore
from core.config import load_environment_config
from core.data import StateCache


class TestBotProfileStore(unittest.TestCase):
    def test_get_or_create_uses_environment_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = TelegramUserProfileStore(cache=StateCache(Path(tmp) / "profiles.json"))
            profile = store.get_or_create(100, load_environment_config("dev"))
            self.assertEqual(profile.user_id, 100)
            self.assertEqual(profile.mode, "signal_only")
            self.assertEqual(profile.exchange, "hyperliquid")
            self.assertEqual(profile.timeframe, "5m")
            self.assertEqual(profile.rr_ratio, 2.0)
            self.assertEqual(profile.max_daily_drawdown_pct, 10.0)
            self.assertEqual(profile.max_open_positions, 1)
            self.assertEqual(profile.sl_pct, 0.5)
            self.assertEqual(profile.tp_pct, 1.0)
            self.assertEqual(profile.open_positions_count, 0)
            self.assertEqual(len(profile.trading_pairs), 1)
            self.assertEqual(profile.trading_pairs[0].symbol, "BTCUSDT")

    def test_profile_persists_across_store_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profiles.json"
            config = load_environment_config("dev")
            first = TelegramUserProfileStore(cache=StateCache(path))
            profile = first.get_or_create(77, config)
            first.save(replace(profile, mode="paper"))

            second = TelegramUserProfileStore(cache=StateCache(path))
            restored = second.get(77)
            self.assertIsNotNone(restored)
            self.assertEqual(restored.mode, "paper")


if __name__ == "__main__":
    unittest.main()
