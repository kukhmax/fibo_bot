import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.backtest import MiniBacktestRunReport
from core.bot import IncomingMessage
from core.bot import TelegramBotRuntime
from core.bot import TelegramUserProfileStore
from core.bot import build_default_router
from core.config import load_environment_config
from core.data import StateCache


class _ScenarioTransport:
    def __init__(self, updates: list[IncomingMessage]) -> None:
        self._updates = list(updates)
        self.sent_messages: list[tuple[int, str]] = []

    def fetch_updates(self, offset: int | None = None, limit: int = 50) -> list[IncomingMessage]:
        if offset is None:
            return self._updates[:limit]
        return [item for item in self._updates if item.update_id >= offset][:limit]

    def send_text(self, chat_id: int, text: str, reply_keyboard=None, inline_keyboard=None) -> None:
        self.sent_messages.append((chat_id, text))


class TestIntegrationMultiAssetBacktest(unittest.IsolatedAsyncioTestCase):
    async def test_backtest_flow_handles_btc_eth_sol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = TelegramUserProfileStore(cache=StateCache(Path(tmp) / "profiles.json"))
            config = load_environment_config("dev")
            router = build_default_router(config, profile_store=store)
            updates = [
                IncomingMessage(update_id=1, chat_id=500, user_id=500, text="/backtest symbol=BTCUSDT timeframe=5m"),
                IncomingMessage(update_id=2, chat_id=500, user_id=500, text="/backtest symbol=ETHUSDT timeframe=5m"),
                IncomingMessage(update_id=3, chat_id=500, user_id=500, text="/backtest symbol=SOLUSDT timeframe=5m"),
            ]
            transport = _ScenarioTransport(updates)
            runtime = TelegramBotRuntime(router=router, transport=transport)
            fake_report = MiniBacktestRunReport(
                candles_count=3000,
                entries_total=120,
                entries_after_ml=90,
                entries_blocked_ml=30,
                trades=90,
                winrate=0.56,
                profit_factor=1.4,
                max_drawdown_r=2.6,
                avg_rr=1.2,
                expectancy_r=0.09,
                is_allowed=True,
                decision_reason="metrics_ok",
                regime_counts={"trend_up": 2000, "range": 800, "volatile": 200},
                strategy_entry_counts={"trend_pullback": 80, "volatility_breakout": 40},
            )
            with (
                patch("core.bot.commands.load_local_backtest_candles", return_value=[object()] * 1200),
                patch("core.bot.commands.load_backtest_candles", return_value=[object()] * 3000),
                patch("core.bot.commands.run_mini_backtest", return_value=fake_report),
            ):
                processed = await runtime.process_once()
            self.assertEqual(processed, 3)
            self.assertEqual(len(transport.sent_messages), 3)
            self.assertIn("symbol=BTCUSDT", transport.sent_messages[0][1])
            self.assertIn("symbol=ETHUSDT", transport.sent_messages[1][1])
            self.assertIn("symbol=SOLUSDT", transport.sent_messages[2][1])
            self.assertTrue(all("asset_status=допущен" in text for (_chat_id, text) in transport.sent_messages))


if __name__ == "__main__":
    unittest.main()
