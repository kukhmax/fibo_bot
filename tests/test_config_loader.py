import unittest

from core.config import load_environment_config


class TestConfigLoader(unittest.TestCase):
    def test_load_dev_profile(self) -> None:
        config = load_environment_config("dev")
        self.assertEqual(config.environment, "dev")
        self.assertEqual(config.exchange.primary, "hyperliquid")
        self.assertEqual(config.exchange.default_timeframe, "5m")
        self.assertLessEqual(config.risk.risk_per_trade_pct, 2.0)

    def test_load_test_profile(self) -> None:
        config = load_environment_config("test")
        self.assertEqual(config.environment, "test")
        self.assertEqual(config.bot.access_mode, "notify_only")

    def test_load_paper_profile(self) -> None:
        config = load_environment_config("paper")
        self.assertEqual(config.environment, "paper")
        self.assertEqual(config.bot.mode, "paper")

    def test_unknown_environment_raises(self) -> None:
        with self.assertRaises(ValueError):
            load_environment_config("unknown")


if __name__ == "__main__":
    unittest.main()
