from pathlib import Path
import tempfile
import unittest
from dataclasses import replace as dc_replace
from unittest.mock import patch

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
        self.assertIn("Добро пожаловать", start.response_text)
        self.assertIn("Текущий статус", status.response_text)
        self.assertIn("Режим", status.response_text)
        self.assertIsNotNone(start.reply_keyboard)

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
        self.assertIn("Режим: paper", updated.response_text)
        self.assertIn("Биржа: mexc", status.response_text)
        self.assertIn("Таймфрейм: 15m", status.response_text)
        self.assertIn("Риск: 1.5%", status.response_text)
        self.assertIn("Интервал отчета: 30", status.response_text)
        
    async def test_toggle_run_starts_and_stops_bot(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        
        # Start
        start_res = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/run on"))
        self.assertIn("ЗАПУЩЕН", start_res.response_text)
        
        profile = self._store.get(42)
        self.assertTrue(profile.is_running)
        
        # Stop
        stop_res = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/run off"))
        self.assertIn("ОСТАНОВЛЕН", stop_res.response_text)
        
        profile = self._store.get(42)
        self.assertFalse(profile.is_running)

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
        self.assertIn("Режим обновлен: paper", mode_result.response_text)
        self.assertIn("Режим: paper", status_result.response_text)

    async def test_set_tf_command_updates_profile(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        tf_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_tf 15m"))
        status_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("Таймфрейм обновлен: 15m", tf_result.response_text)
        self.assertIn("Таймфрейм: 15m", status_result.response_text)

    async def test_set_risk_command_updates_profile(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        risk_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_risk 1.2"))
        status_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("Риск на сделку обновлен: 1.2%", risk_result.response_text)
        self.assertIn("Риск: 1.2%", status_result.response_text)

    async def test_set_risk_command_rejects_invalid_value(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_risk 2.01"))
        self.assertIn("Ошибка обновления профиля", result.response_text)
        self.assertIn("risk должен быть в диапазоне 0.1..2.0", result.response_text)

    async def test_set_rr_command_updates_profile(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        rr_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_rr 2.5"))
        status_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("Risk/Reward обновлен: 2.5", rr_result.response_text)
        self.assertIn("RR: 2.5", status_result.response_text)

    async def test_set_dd_command_updates_profile(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        dd_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_dd 20"))
        status_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("Лимит дневной просадки обновлен: 20.0%", dd_result.response_text)
        self.assertIn("DD: 20.0%", status_result.response_text)

    async def test_set_maxpos_command_updates_profile(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        maxpos_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_maxpos 3"))
        status_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("Лимит открытых позиций обновлен: 3", maxpos_result.response_text)
        self.assertIn("Макс. позиций: 3", status_result.response_text)

    async def test_set_sl_tp_commands_update_profile(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        sl_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_sl 0.8"))
        tp_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_tp 1.6"))
        status_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("Стоп-лосс обновлен: 0.8%", sl_result.response_text)
        self.assertIn("Тейк-профит обновлен: 1.6%", tp_result.response_text)
        self.assertIn("SL: 0.8%", status_result.response_text)
        self.assertIn("TP: 1.6%", status_result.response_text)

    async def test_close_command_decrements_open_positions(self) -> None:
        config = load_environment_config("dev")
        profile = self._store.get_or_create(42, config)
        self._store.save(dc_replace(profile, open_positions_count=2))
        router = build_default_router(config, profile_store=self._store)
        close_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/close"))
        status_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("Позиция закрыта", close_result.response_text)
        self.assertIn("Открытых позиций: 1", status_result.response_text)

    async def test_risk_menu_returns_reply_keyboard(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/risk"))
        self.assertTrue(result.handled)
        self.assertIn("Меню риска", result.response_text)
        self.assertIsNotNone(result.reply_keyboard)
        assert result.reply_keyboard is not None
        labels = [label for row in result.reply_keyboard for label in row]
        self.assertTrue(any("Настроить Risk" in label for label in labels))
        self.assertTrue(any("Настроить RR" in label for label in labels))
        self.assertTrue(any("Настроить DD" in label for label in labels))

    async def test_menu_has_human_friendly_buttons(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/menu"))
        self.assertTrue(result.handled)
        self.assertIn("Главное меню", result.response_text)
        self.assertIsNotNone(result.reply_keyboard)
        assert result.reply_keyboard is not None
        labels = [title for row in result.reply_keyboard for title in row]
        self.assertTrue(any("🛡" in item for item in labels))
        self.assertFalse(any("⏱" in item for item in labels))  # Timeframe should be gone

    async def test_mode_menu_returns_reply_keyboard_with_emojis(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/mode_menu"))
        self.assertTrue(result.handled)
        self.assertIn("Настройка режима работы", result.response_text)
        self.assertIsNotNone(result.reply_keyboard)
        assert result.reply_keyboard is not None
        labels = [label for row in result.reply_keyboard for label in row]
        self.assertTrue(any("🔔 Только сигналы" in label for label in labels))
        self.assertTrue(any("🧪 Paper" in label for label in labels))
        self.assertTrue(any("🔥 Live" in label for label in labels))

    async def test_mode_reply_keyboard_buttons_dispatch_commands(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        
        signal_res = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="🔔 Только сигналы"))
        paper_res = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="🧪 Paper"))
        live_res = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="🔥 Live"))
        
        self.assertIn("Режим обновлен: signal_only", signal_res.response_text)
        self.assertIn("Режим обновлен: paper", paper_res.response_text)
        self.assertIn("Режим обновлен: live", live_res.response_text)

    async def test_reply_keyboard_text_button_dispatches_command(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="📊 Статус"))
        self.assertTrue(result.handled)
        self.assertIn("Текущий статус", result.response_text)

    async def test_reply_keyboard_tf_and_risk_presets_dispatch_commands(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        tf_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="🚀 TF 5m"))
        risk_result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="🛡 Risk 1.0%"))
        self.assertIn("Таймфрейм обновлен: 5m", tf_result.response_text)
        self.assertIn("Риск на сделку обновлен: 1.0%", risk_result.response_text)

    async def test_pairs_add_list_remove_flow(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        added = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/pair_add ETHUSDT 15m"))
        listed = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/pairs"))
        removed = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/pair_remove ETHUSDT"))
        self.assertIn("Пара добавлена: ETHUSDT", added.response_text)
        self.assertIn("ETHUSDT • 15m", listed.response_text)
        self.assertIn("Пара удалена: ETHUSDT", removed.response_text)

    async def test_pairs_button_flow_add_and_delete(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        add_prompt = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="➕ Добавить пару"))
        self.assertIn("Введи одним сообщением", add_prompt.response_text)
        add_from_text = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="SOLUSDT 1m"))
        self.assertIn("Пара добавлена: SOLUSDT", add_from_text.response_text)
        remove_menu = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="➖ Удалить пару"))
        self.assertIsNotNone(remove_menu.inline_keyboard)
        assert remove_menu.inline_keyboard is not None
        callbacks = [cb for row in remove_menu.inline_keyboard for (_title, cb) in row]
        self.assertIn("/pair_delete SOLUSDT", callbacks)

    async def test_hide_menu_removes_reply_keyboard(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/hide_menu"))
        self.assertTrue(result.handled)
        self.assertEqual(result.reply_keyboard, ())
        self.assertIn("Меню скрыто", result.response_text)

    async def test_tf_menu_returns_timeframe_buttons(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/tf_menu"))
        self.assertTrue(result.handled)
        self.assertIn("Выбор таймфрейма", result.response_text)
        self.assertIsNotNone(result.inline_keyboard)
        assert result.inline_keyboard is not None
        callbacks = [callback for row in result.inline_keyboard for (_text, callback) in row]
        self.assertIn("/set_tf 1m", callbacks)
        self.assertIn("/set_tf 4h", callbacks)

    async def test_risk_submenus_return_presets_and_back(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        risk_values = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/risk_risk"))
        rr_values = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/risk_rr"))
        dd_values = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/risk_dd"))
        self.assertIn("Настройка Risk", risk_values.response_text)
        self.assertIn("Введи число", risk_values.response_text)
        self.assertIn("Настройка Risk/Reward", rr_values.response_text)
        self.assertIn("Введи число", rr_values.response_text)
        self.assertIn("Настройка дневной просадки", dd_values.response_text)
        
        assert risk_values.reply_keyboard is not None
        risk_labels = [label for row in risk_values.reply_keyboard for label in row]
        self.assertFalse(any("Risk 1.0%" in label for label in risk_labels))
        self.assertTrue(any("Назад" in label for label in risk_labels))

    async def test_readiness_reports_missing_secrets(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/readiness"))
        self.assertTrue(result.handled)
        self.assertIn("Готовность к live-этапу", result.response_text)
        self.assertIn("❌ Ключи Hyperliquid заданы", result.response_text)

    async def test_readiness_reports_ok_when_live_and_secrets_present(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_BOT_TOKEN": "token123",
                "HYPERLIQUID_API_KEY": "hl_key",
                "HYPERLIQUID_API_SECRET": "hl_secret",
            },
            clear=False,
        ):
            await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/mode live"))
            result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/readiness"))
        self.assertTrue(result.handled)
        self.assertIn("✅ Режим live активирован", result.response_text)
        self.assertIn("✅ Ключи Hyperliquid заданы", result.response_text)

    async def test_news_command_returns_news_engine_status(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        with patch.dict("os.environ", {"NEWS_SOURCE": "t.me/cryptoarsenal", "NEWS_FILTER_ENABLED": "1"}, clear=False):
            result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/news"))
        self.assertTrue(result.handled)
        self.assertIn("News engine", result.response_text)
        self.assertIn("source=t.me/cryptoarsenal", result.response_text)

    async def test_backtest_menu_returns_reply_keyboard(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/backtest"))
        self.assertTrue(result.handled)
        self.assertIn("Mini-Backtest", result.response_text)
        self.assertIsNotNone(result.reply_keyboard)
        assert result.reply_keyboard is not None
        labels = [label for row in result.reply_keyboard for label in row]
        self.assertTrue(any("BTCUSDT 5m" in label for label in labels))

    @patch("core.bot.commands.load_backtest_candles")
    @patch("core.bot.commands.load_local_backtest_candles")
    async def test_backtest_accepts_symbol_and_timeframe(self, mock_local, mock_remote) -> None:
        # Mock candles to ensure backtest runs
        from core.data.models import Candle
        mock_candles = [
            Candle(
                symbol="BTCUSDT", 
                timeframe="5m", 
                open_time_ms=10000+i*60000, 
                close_time_ms=10000+i*60000+59999, 
                open=100.0, 
                high=110.0, 
                low=90.0, 
                close=105.0, 
                volume=1000.0
            ) for i in range(100)
        ]
        mock_remote.return_value = mock_candles
        mock_local.return_value = []

        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(
            CommandContext(chat_id=1, user_id=42, text="/backtest symbol=BTCUSDT timeframe=5m")
        )
        self.assertTrue(result.handled)
        self.assertIn("Symbol: BTCUSDT", result.response_text)
        self.assertIn("Timeframe: 5m", result.response_text)
        self.assertIn("🧪 Mini-Backtest отчет", result.response_text)
        self.assertIn("Параметры", result.response_text)
        self.assertIn("Сигналы", result.response_text)
        self.assertIn("Метрики", result.response_text)
        self.assertIn("Total:", result.response_text)
        self.assertIn("Trades:", result.response_text)
        self.assertIn("Winrate:", result.response_text)
        self.assertIn("Итог", result.response_text)
        self.assertIn("Status:", result.response_text)

    async def test_backtest_flow_manual_input(self) -> None:
        config = load_environment_config("dev")
        router = build_default_router(config, profile_store=self._store)
        
        # Step 1: Start backtest flow
        prompt = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/backtest"))
        self.assertIn("Выбери пару из списка или напиши свою", prompt.response_text)
        
        # Step 2: Send manual input
        result = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="DOGEUSDT 15m"))
        self.assertTrue(result.handled)
        # Since we haven't mocked load_backtest_candles for this test case, it will fail to load
        # But we want to ensure it TRIED to run backtest
        self.assertTrue(
            "Не удалось загрузить данные" in result.response_text 
            or "Mini-Backtest отчет" in result.response_text
        )

    async def test_notify_only_access_blocks_updates(self) -> None:
        config = load_environment_config("dev")
        config = dc_replace(config, bot=dc_replace(config.bot, access_mode="notify_only"))
        router = build_default_router(config, profile_store=self._store)
        blocked_mode = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/mode paper"))
        blocked_risk = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/set_risk 1.2"))
        status = await router.dispatch(CommandContext(chat_id=1, user_id=42, text="/status"))
        self.assertIn("notify_only", blocked_mode.response_text)
        self.assertIn("notify_only", blocked_risk.response_text)
        self.assertIn("Режим: signal_only", status.response_text)

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
        self.assertIn("Модель не найдена", result.response_text)
        self.assertIsNotNone(result.inline_keyboard)

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
        self.assertIn("Train: 75.00%", result.response_text)
        self.assertIn("Validation: 66.00%", result.response_text)
        self.assertIsNotNone(result.inline_keyboard)

    @patch("core.bot.commands.MlTrainingPipeline.run")
    @patch("core.bot.commands.MlTrainDatasetBuilder")
    @patch("core.bot.commands.HistoricalTrainingDataPipeline")
    async def test_ml_train_runs_pipeline_and_returns_success(self, _mock_hist, _mock_ds, mock_run) -> None:
        from core.ml.artifacts import BaselineModelArtifact
        config = load_environment_config("dev")
        
        # Mock successful training
        mock_artifact = BaselineModelArtifact(
            feature_names=("f1",), weights=(1.0,), bias=0.0,
            train_accuracy=0.8, validation_accuracy=0.7,
            train_size=100, validation_size=20
        )
        mock_run.return_value = mock_artifact
        
        router = build_default_router(config, profile_store=self._store)
        result = await router.dispatch(CommandContext(chat_id=1, user_id=2, text="/ml_train"))
        
        self.assertTrue(result.handled)
        self.assertIn("Обучение завершено", result.response_text)
        self.assertIn("Accuracy: 70.00%", result.response_text)
        mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
