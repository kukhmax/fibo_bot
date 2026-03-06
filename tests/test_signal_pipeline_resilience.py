import asyncio
from dataclasses import replace as dc_replace
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from core.bot.main import _run_app
from core.bot.profile import TelegramUserProfileStore
from core.config import load_environment_config
from core.data import Candle
from core.data import StateCache


class _FakeTransport:
    def __init__(self) -> None:
        self.sent_messages: list[tuple[int, str]] = []

    def send_text(self, chat_id: int, text: str) -> None:
        self.sent_messages.append((chat_id, text))


class _FakeRuntime:
    pass


class _ClassifierStub:
    def classify(self, candles: list[Candle]) -> SimpleNamespace:
        return SimpleNamespace(label="trend_up", confidence=0.9)


class _StrategyStub:
    def on_candle(self, candle: Candle) -> SimpleNamespace:
        return SimpleNamespace(
            action="entry",
            direction="BUY",
            strategy="trend_pullback",
            explain="stub_entry",
        )


class _PipelineStub:
    latest: "_PipelineStub | None" = None

    def __init__(self, symbol: str, timeframe: str, on_candle) -> None:  # type: ignore[no-untyped-def]
        self.symbol = symbol
        self.timeframe = timeframe
        self._on_candle = on_candle
        self._runs = 0
        _PipelineStub.latest = self

    async def run(self) -> None:
        self._runs += 1
        if self._runs <= 2:
            raise RuntimeError("source_unavailable")
        candle = Candle(
            symbol="BTCUSDT",
            timeframe="5m",
            open_time_ms=1_000,
            close_time_ms=1_299,
            open=100.0,
            high=101.0,
            low=99.5,
            close=100.6,
            volume=123.0,
        )
        await self._on_candle(candle)
        raise asyncio.CancelledError()


class TestSignalPipelineResilience(unittest.IsolatedAsyncioTestCase):
    async def test_run_app_survives_source_errors_and_keeps_modes_working(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_sleep = asyncio.sleep
            config = load_environment_config("dev")
            config = dc_replace(config, ml=dc_replace(config.ml, enabled=False))
            store = TelegramUserProfileStore(cache=StateCache(Path(tmp) / "profiles.json"))
            signal_profile = store.get_or_create(1001, config)
            paper_profile = store.get_or_create(1002, config)
            store.save(dc_replace(signal_profile, mode="signal_only"))
            store.save(dc_replace(paper_profile, mode="paper", max_open_positions=3, open_positions_count=0))
            transport = _FakeTransport()

            async def _runtime_stub(runtime, once: bool) -> None:  # type: ignore[no-untyped-def]
                await original_sleep(0)

            async def _fast_sleep(_seconds: float) -> None:
                await original_sleep(0)

            with (
                patch.dict("os.environ", {"ENABLE_SIGNALS": "1", "FIB_SYMBOL": "BTCUSDT", "FIB_STRATEGY": "auto_regime"}),
                patch("core.bot.main._run_runtime", _runtime_stub),
                patch("core.bot.main.asyncio.sleep", _fast_sleep),
                patch("core.bot.main.RealtimeCandlePipeline", _PipelineStub),
                patch("core.bot.main.RuleBasedRegimeClassifier", _ClassifierStub),
                patch("core.bot.main.TrendPullbackStrategy", _StrategyStub),
                patch("core.bot.main.VolatilityBreakoutStrategy", _StrategyStub),
                patch("core.bot.main.LiquiditySweepReversalStrategy", _StrategyStub),
                patch("core.bot.main.select_strategy_by_regime", return_value="trend_pullback"),
            ):
                with self.assertRaises(asyncio.CancelledError):
                    await _run_app(
                        runtime=_FakeRuntime(),
                        transport=transport,  # type: ignore[arg-type]
                        store=store,
                        config_env=config,
                        once=False,
                    )

            self.assertIsNotNone(_PipelineStub.latest)
            assert _PipelineStub.latest is not None
            self.assertGreaterEqual(_PipelineStub.latest._runs, 3)
            recipients = [chat_id for (chat_id, _text) in transport.sent_messages]
            self.assertIn(1001, recipients)
            self.assertIn(1002, recipients)
            updated_paper = store.get(1002)
            assert updated_paper is not None
            self.assertEqual(updated_paper.open_positions_count, 1)


if __name__ == "__main__":
    unittest.main()
