from pathlib import Path
import tempfile
import unittest
from dataclasses import replace as dc_replace

from core.bot import CommandContext
from core.bot import CommandRouter
from core.bot import IncomingMessage
from core.bot import TelegramBotRuntime
from core.bot import TelegramUserProfileStore
from core.bot import build_default_router
from core.config import load_environment_config
from core.data import StateCache
from core.ml.artifacts import ModelArtifactStore
from core.ml.model import BaselineProbabilityModel
from core.ml.trainer import TrainingReport


class _FakeTransport:
    def __init__(self, updates: list[IncomingMessage]) -> None:
        self._updates = list(updates)
        self.sent_messages: list[tuple[int, str, tuple[tuple[str, ...], ...] | None, tuple[tuple[tuple[str, str], ...], ...] | None]] = []

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


class TestBotRouter(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._store = TelegramUserProfileStore(cache=StateCache(Path(self._tmp.name) / "profiles.json"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

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
        router = build_default_router(config, profile_store=self._store)
        start = await router.dispatch(CommandContext(chat_id=1, user_id=2, text="/start"))
        status = await router.dispatch(CommandContext(chat_id=1, user_id=2, text="/status"))
        self.assertTrue(start.handled)
        self.assertTrue(status.handled)
        self.assertIn("fib_bot готов", start.response_text)
        self.assertIn("online", status.response_text)
        self.assertIn("mode=", status.response_text)
        self.assertIsNotNone(start.reply_keyboard)
        self.assertIn("/status", start.reply_keyboard[0])

    async def test_start_updates_master_profile(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        updated = await router.dispatch(
            CommandContext(
                chat_id=1,
                user_id=42,
                text="/start mode=paper exchange=mexc timeframe=15m risk=1.5 report=30",
            )
        )
        status = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertTrue(updated.handled)
        self.assertIn("mode=paper", updated.response_text)
        self.assertIn("exchange=mexc", status.response_text)
        self.assertIn("timeframe=15m", status.response_text)
        self.assertIn("risk=1.5", status.response_text)
        self.assertIn("report_interval_min=30", status.response_text)

    async def test_start_rejects_invalid_profile_values(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/start risk=9"))
        self.assertTrue(result.handled)
        self.assertIn("Ошибка обновления профиля", result.response_text)

    async def test_mode_command_updates_profile(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        mode_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/mode paper"))
        status_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("mode обновлен: paper", mode_result.response_text)
        self.assertIn("mode=paper", status_result.response_text)

    async def test_set_tf_command_updates_profile(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        tf_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_tf 15m"))
        status_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("timeframe обновлен: 15m", tf_result.response_text)
        self.assertIn("timeframe=15m", status_result.response_text)

    async def test_set_risk_command_updates_profile(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        risk_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_risk 1.2"))
        status_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("risk обновлен: 1.2", risk_result.response_text)
        self.assertIn("risk=1.2", status_result.response_text)

    async def test_set_risk_command_rejects_invalid_value(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_risk 9"))
        self.assertIn("Ошибка обновления профиля", result.response_text)
        self.assertIn("risk должен быть в диапазоне 0.1..2.0", result.response_text)

    async def test_notify_only_access_blocks_updates(self) -> None:
        config = load_environment_config("dev")
        config = dc_replace(config, bot=dc_replace(config.bot, access_mode="notify_only"))
        router = build_default_router(config, profile_store=self._store)
        blocked_mode = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/mode paper"))
        blocked_risk = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_risk 1.2"))
        status = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("notify_only", blocked_mode.response_text)
        self.assertIn("notify_only", blocked_risk.response_text)
        self.assertIn("mode=signal_only", status.response_text)

    async def test_runtime_fetches_updates_and_sends_responses(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
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
        self.assertIsNotNone(transport.sent_messages[0][2])
        self.assertIsNone(transport.sent_messages[0][3])

    async def test_ml_report_returns_not_found_without_artifact(self) -> None:
        config = load_environment_config("dev")
        store = ModelArtifactStore(Path(self._tmp.name) / "missing_model.json")
        router = build_default_router(config, profile_store=self._store, ml_artifact_store=store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=2, text="/ml_report"))
        self.assertTrue(result.handled)
        self.assertIn("ML отчет", result.response_text)
        self.assertIn("artifact=not_found", result.response_text)

    async def test_ml_report_returns_metrics_when_artifact_exists(self) -> None:
        config = load_environment_config("dev")
        store = ModelArtifactStore(Path(self._tmp.name) / "baseline_model.json")
        model = BaselineProbabilityModel(
            feature_names=("ret_1", "range_pct", "body_pct", "sma_ratio", "volume"),
            weights=(0.1, 0.2, -0.1, 0.05, 0.01),
            bias=0.0,
        )
        report = TrainingReport(
            train_accuracy=0.75,
            validation_accuracy=0.66,
            train_size=120,
            validation_size=30,
        )
        store.save(model, report)
        router = build_default_router(config, profile_store=self._store, ml_artifact_store=store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=2, text="/ml_report"))
        self.assertTrue(result.handled)
        self.assertIn("train_accuracy=0.7500", result.response_text)
        self.assertIn("validation_accuracy=0.6600", result.response_text)


if __name__ == "__main__":
    unittest.main()
