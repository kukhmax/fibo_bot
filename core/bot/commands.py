from dataclasses import replace
import os

from core.bot.router import CommandContext
from core.bot.router import CommandRouter
from core.bot.profile import TelegramUserProfile
from core.bot.profile import TelegramUserProfileStore
from core.bot.profile import TradingPairSettings
from core.backtest import load_backtest_candles
from core.backtest import load_local_backtest_candles
from core.backtest import run_mini_backtest
from core.config.models import EnvironmentConfig
from core.ml.artifacts import ModelArtifactStore
from core.ml.inference import MlSignalFilter
from core.bot.reporter import MiniBacktestReporter
from core.bot.reporter import MlQualityReporter
from core.bot.reporter import PositionReporter
from core.bot.news_engine import NewsRiskGate
from core.data.persistence import StateCache
from core.risk import RiskManager


from core.ml.dataset_builder import MlTrainDatasetBuilder
from core.ml.history_pipeline import HistoricalTrainingDataPipeline
from core.ml.training_pipeline import MlTrainingPipeline


RISK_MANAGER = RiskManager()
BACKTEST_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
BACKTEST_TIMEFRAMES: tuple[str, ...] = ("1m", "5m", "15m", "1h")


def build_default_router(
    config: EnvironmentConfig,
    profile_store: TelegramUserProfileStore | None = None,
    ml_artifact_store: ModelArtifactStore | None = None,
) -> CommandRouter:
    router = CommandRouter()
    router.set_reply_keyboard(_main_menu_reply())
    store = profile_store or TelegramUserProfileStore()
    ml_reporter = MlQualityReporter(artifact_store=ml_artifact_store)
    pair_flow_state = StateCache("runtime/pair_flow_state.json")

    def _flow_key(user_id: int) -> str:
        return f"flow:{user_id}"

    def _set_flow(user_id: int, action: str) -> None:
        pair_flow_state.set(_flow_key(user_id), {"action": action})

    def _get_flow(user_id: int) -> str:
        payload = pair_flow_state.get(_flow_key(user_id))
        if not isinstance(payload, dict):
            return ""
        return str(payload.get("action", "")).strip().lower()

    def _clear_flow(user_id: int) -> None:
        pair_flow_state.set(_flow_key(user_id), {})

    def start_handler(ctx: CommandContext, args: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        if args.strip():
            if not _access_write_allowed(config):
                return {"text": "🔒 Сейчас только режим уведомлений, менять настройки нельзя."}
            updated, errors = _apply_start_updates(profile, args)
            if errors:
                return {"text": _format_profile_error(profile, errors)}
            store.save(updated)
            profile = updated
        text = (
            "👋 Добро пожаловать в Fibo Bot\n"
            "Я помогу настроить сигналы и риск простыми шагами.\n\n"
            f"📌 Режим: {profile.mode}\n"
            f"📈 Биржа: {profile.exchange}\n"
            f"⏱ Таймфрейм: {profile.timeframe}\n"
            f"🛡 Риск на сделку: {profile.risk_per_trade_pct}%\n"
            f"🎯 Risk/Reward: {profile.rr_ratio}\n"
            f"🚫 Дневная просадка: {profile.max_daily_drawdown_pct}%\n"
            f"📦 Макс. открытых позиций: {profile.max_open_positions}\n"
            f"🧯 Стоп-лосс: {profile.sl_pct}%\n"
            f"💰 Тейк-профит: {profile.tp_pct}%\n"
            f"🔔 Отчёт каждые: {profile.position_report_minutes} мин\n\n"
            "Выбери действие кнопками ниже 👇"
        )
        return {"text": text}

    def help_handler(_: CommandContext, __: str) -> str:
        return (
            "❓ Как пользоваться ботом\n"
            "1) Нажми /start — увидишь главное меню\n"
            "2) Выбери ⏱ Таймфрейм и 🛡 Риск\n"
            "3) Настрой 🎯 RR, 🚫 DD и 📦 лимит позиций в меню риска\n"
            "4) Проверь профиль через 📊 Статус\n"
            "5) Запусти 🧪 Mini-backtest для проверки актива\n\n"
            "Команды для быстрого доступа:\n"
            "/status /pairs /pair_add BTCUSDT 5m /pair_remove BTCUSDT /risk /tf_menu /mode_menu /backtest /positions /ml_report /readiness /hide_menu"
        )

    def hide_menu_handler(_: CommandContext, __: str) -> dict:
        return {"text": "Меню скрыто. Чтобы вернуть кнопки, нажми /menu.", "reply_keyboard": ()}

    def mode_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_mode = args.strip().lower()
        if not raw_mode:
            return f"🤖 Текущий режим: {profile.mode}\nВыбери кнопкой: /mode_menu"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        mode = _parse_mode(raw_mode, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, mode=mode)
        store.save(updated)
        return f"✅ Режим обновлен: {updated.mode}"

    def set_tf_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_timeframe = args.strip().lower()
        if not raw_timeframe:
            return f"⏱ Текущий таймфрейм: {profile.timeframe}\nОткрой выбор: /tf_menu"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        timeframe = _parse_timeframe(raw_timeframe, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, timeframe=timeframe)
        store.save(updated)
        return f"✅ Таймфрейм обновлен: {updated.timeframe}"

    def set_risk_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_risk = args.strip()
        if not raw_risk:
            return f"🛡 Текущий риск на сделку: {profile.risk_per_trade_pct}%\nОткрой меню риска: /risk"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        risk = _parse_risk(raw_risk, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, risk_per_trade_pct=risk)
        store.save(updated)
        return f"✅ Риск на сделку обновлен: {updated.risk_per_trade_pct}%"

    def set_rr_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_rr = args.strip()
        if not raw_rr:
            return f"🎯 Текущий Risk/Reward: {profile.rr_ratio}\nОткрой меню риска: /risk"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        rr = _parse_rr(raw_rr, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, rr_ratio=rr)
        store.save(updated)
        return f"✅ Risk/Reward обновлен: {updated.rr_ratio}"

    def set_dd_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_dd = args.strip()
        if not raw_dd:
            return f"🚫 Текущий дневной лимит просадки: {profile.max_daily_drawdown_pct}%\nОткрой меню риска: /risk"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        max_dd = _parse_max_daily_drawdown(raw_dd, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, max_daily_drawdown_pct=max_dd)
        store.save(updated)
        return f"✅ Лимит дневной просадки обновлен: {updated.max_daily_drawdown_pct}%"

    def set_maxpos_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_maxpos = args.strip()
        if not raw_maxpos:
            return f"📦 Текущий лимит открытых позиций: {profile.max_open_positions}\nОткрой меню риска: /risk"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        max_pos = _parse_max_open_positions(raw_maxpos, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, max_open_positions=max_pos)
        store.save(updated)
        return f"✅ Лимит открытых позиций обновлен: {updated.max_open_positions}"

    def set_sl_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_sl = args.strip()
        if not raw_sl:
            return f"🧯 Текущий стоп-лосс: {profile.sl_pct}%\nОткрой меню риска: /risk"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        sl = _parse_sl_pct(raw_sl, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, sl_pct=sl)
        store.save(updated)
        return f"✅ Стоп-лосс обновлен: {updated.sl_pct}%"

    def set_tp_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_tp = args.strip()
        if not raw_tp:
            return f"💰 Текущий тейк-профит: {profile.tp_pct}%\nОткрой меню риска: /risk"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        tp = _parse_tp_pct(raw_tp, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, tp_pct=tp)
        store.save(updated)
        return f"✅ Тейк-профит обновлен: {updated.tp_pct}%"

    def close_handler(ctx: CommandContext, __: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        if profile.open_positions_count <= 0:
            return "Нет открытых позиций для закрытия."
        updated = replace(profile, open_positions_count=max(0, profile.open_positions_count - 1))
        store.save(updated)
        return f"Позиция закрыта. Открытых позиций: {updated.open_positions_count}"

    def status_handler(ctx: CommandContext, __: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        pairs_text = ", ".join(f"{pair.symbol}:{pair.timeframe}" for pair in profile.trading_pairs)
        return (
            "📊 Текущий статус\n"
            f"🔐 Доступ: {config.bot.access_mode}\n"
            f"🤖 Режим: {profile.mode}\n"
            f"📈 Биржа: {profile.exchange}\n"
            f"⏱ Таймфрейм: {profile.timeframe}\n"
            f"🛡 Риск: {profile.risk_per_trade_pct}%\n"
            f"🎯 RR: {profile.rr_ratio}\n"
            f"🚫 DD: {profile.max_daily_drawdown_pct}%\n"
            f"📦 Макс. позиций: {profile.max_open_positions}\n"
            f"🧯 SL: {profile.sl_pct}%\n"
            f"💰 TP: {profile.tp_pct}%\n"
            f"🧩 Пары: {pairs_text}\n"
            f"📍 Открытых позиций: {profile.open_positions_count}\n"
            f"🔔 Интервал отчета: {profile.position_report_minutes} мин"
        )

    def pairs_handler(ctx: CommandContext, __: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        lines = ["🧩 Торговые пары", "━━━━━━━━━━━━━━"]
        for index, pair in enumerate(profile.trading_pairs, start=1):
            lines.append(f"{index}) {pair.symbol} • {pair.timeframe}")
        lines.append("")
        lines.append("Управление парами 👇")
        return {"text": "\n".join(lines), "reply_keyboard": _pairs_menu_reply()}

    def pair_add_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        if not args.strip():
            _set_flow(ctx.user_id, "await_pair_add")
            return (
                "➕ Добавление пары\n"
                "Введи одним сообщением: SYMBOL TIMEFRAME\n"
                "Пример: BTCUSDT 5m"
            )
        symbol, timeframe, errors = _parse_pair_args(args)
        if errors:
            return _format_profile_error(profile, errors)
        merged = {item.symbol: item for item in profile.trading_pairs}
        merged[symbol] = TradingPairSettings(symbol=symbol, timeframe=timeframe)
        updated_pairs = tuple(merged[key] for key in sorted(merged))
        updated = replace(profile, trading_pairs=updated_pairs)
        store.save(updated)
        _clear_flow(ctx.user_id)
        return f"✅ Пара добавлена: {symbol} • {timeframe}\nВсего пар: {len(updated_pairs)}"

    def pair_remove_handler(ctx: CommandContext, args: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        if not _access_write_allowed(config):
            return {"text": "Режим доступа notify_only: команда недоступна."}
        if not args.strip():
            buttons: list[tuple[str, str]] = []
            for pair in profile.trading_pairs:
                buttons.append((f"❌ {pair.symbol} • {pair.timeframe}", f"/pair_delete {pair.symbol}"))
            if not buttons:
                return {"text": "Список пар пуст."}
            inline = tuple((item,) for item in buttons)
            return {"text": "➖ Удаление пары\nВыбери пару для удаления:", "inline_keyboard": inline}
        symbol = args.strip().upper()
        if not symbol:
            return {"text": "Укажи пару: /pair_remove BTCUSDT"}
        current = [item for item in profile.trading_pairs if item.symbol != symbol]
        if len(current) == len(profile.trading_pairs):
            return {"text": f"Пара не найдена: {symbol}"}
        if not current:
            current = [TradingPairSettings(symbol="BTCUSDT", timeframe=profile.timeframe)]
        updated = replace(profile, trading_pairs=tuple(current))
        store.save(updated)
        return {"text": f"✅ Пара удалена: {symbol}\nОсталось пар: {len(updated.trading_pairs)}"}

    def pair_delete_handler(ctx: CommandContext, args: str) -> dict:
        return pair_remove_handler(ctx, args)

    def text_handler(ctx: CommandContext, args: str) -> str:
        action = _get_flow(ctx.user_id)
        if action == "await_risk":
            return set_risk_handler(ctx, args)
        elif action == "await_rr":
            return set_rr_handler(ctx, args)
        elif action == "await_dd":
            return set_dd_handler(ctx, args)
        elif action == "await_maxpos":
            return set_maxpos_handler(ctx, args)
        elif action == "await_sl":
            return set_sl_handler(ctx, args)
        elif action == "await_tp":
            return set_tp_handler(ctx, args)
        elif action == "await_pair_add":
            symbol, timeframe, errors = _parse_pair_args(args)
            if errors:
                return "Неверный формат. Введи так: BTCUSDT 5m"
            return pair_add_handler(ctx, f"{symbol} {timeframe}")
        elif action == "await_backtest":
            # The backtest command expects "symbol=... timeframe=..."
            # But the user will type "BTCUSDT 5m" or just "BTCUSDT"
            # We need to parse this and convert it to "symbol=... timeframe=..."
            symbol, timeframe, errors = _parse_pair_args(args)
            if errors:
                return "Неверный формат. Введи так: BTCUSDT 5m"
            return backtest_handler(ctx, f"symbol={symbol} timeframe={timeframe}")
        
        return "Команда не распознана."

    def readiness_handler(ctx: CommandContext, __: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        checks = [
            ("Режим live активирован", profile.mode == "live"),
            ("Полный доступ бота", config.bot.access_mode == "full_access"),
            ("Токен Telegram задан", _is_secret_configured(os.getenv("TELEGRAM_BOT_TOKEN", ""))),
            (
                "Ключи Hyperliquid заданы",
                _is_secret_configured(os.getenv("HYPERLIQUID_API_KEY", ""))
                and _is_secret_configured(os.getenv("HYPERLIQUID_API_SECRET", "")),
            ),
        ]
        lines = ["🧭 Готовность к live-этапу"]
        not_ready = 0
        for title, ok in checks:
            lines.append(f"{'✅' if ok else '❌'} {title}")
            if not ok:
                not_ready += 1
        if not_ready == 0:
            lines.append("🚀 Можно переходить к live-подключению.")
        else:
            lines.append(f"⚠️ Нужно закрыть пунктов: {not_ready}")
        lines.append("Подсказка: /mode live, затем проверь /status.")
        return "\n".join(lines)

    def news_handler(_: CommandContext, __: str) -> str:
        source = os.getenv("NEWS_SOURCE", "t.me/cryptoarsenal").strip()
        enabled = bool(os.getenv("NEWS_FILTER_ENABLED", "1"))
        keywords = tuple(
            item.strip()
            for item in os.getenv(
                "NEWS_RISK_KEYWORDS",
                "hack,exploit,bankrupt,bankruptcy,liquidation,delist,lawsuit,outage",
            ).split(",")
            if item.strip()
        )
        gate = NewsRiskGate(source=source, keywords=keywords, min_block_score=int(os.getenv("NEWS_BLOCK_MIN_SCORE", "1")))
        return (
            "📰 News engine\n"
            f"source={gate.source}\n"
            f"enabled={enabled}\n"
            f"keywords={','.join(gate.keywords)}\n"
            f"min_block_score={gate.min_block_score}"
        )

    def positions_handler(ctx: CommandContext, __: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        text = PositionReporter().build_report(profile)
        inline = ((( "Обновить", "/positions"),),)
        return {"text": text, "inline_keyboard": inline}

    def ml_report_handler(_: CommandContext, __: str) -> dict:
        text = ml_reporter.build_report()
        # Always offer training button
        inline = ((("🚀 Обучить модель", "/ml_train"),),)
        return {"text": text, "inline_keyboard": inline}

    def ml_train_handler(ctx: CommandContext, __: str) -> str:
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: обучение недоступно."
        
        # For MVP, we train on a default pair to get a general model
        symbol = "BTCUSDT"
        timeframe = "5m"
        
        pipeline = MlTrainingPipeline(
            dataset_builder=MlTrainDatasetBuilder(
                history_pipeline=HistoricalTrainingDataPipeline(
                    symbol=symbol, 
                    timeframe=timeframe,
                    min_candles=3000
                )
            ),
            artifact_store=ml_artifact_store
        )
        
        try:
            artifact = pipeline.run(candle_limit=3000, epochs=50)
            return (
                f"✅ **Обучение завершено!**\n"
                f"Модель сохранена.\n\n"
                f"🎯 Accuracy: {artifact.validation_accuracy:.2%}\n"
                f"📊 Samples: {artifact.train_size + artifact.validation_size}\n"
                f"Параметры: {symbol} {timeframe}"
            )
        except Exception as e:
            return f"❌ Ошибка обучения: {str(e)}"

    def risk_menu_handler(ctx: CommandContext, __: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "🛡 Меню риска\n"
            f"🛡 Risk: {profile.risk_per_trade_pct}%\n"
            f"🎯 RR: {profile.rr_ratio}\n"
            f"🚫 DD: {profile.max_daily_drawdown_pct}%\n"
            f"📦 MaxPos: {profile.max_open_positions}\n"
            f"🧯 SL: {profile.sl_pct}%\n"
            f"💰 TP: {profile.tp_pct}%\n"
            "Выбери раздел настройки:"
        )
        return {"text": text, "reply_keyboard": _risk_menu_reply()}

    def risk_risk_handler(ctx: CommandContext, __: str) -> dict:
        _set_flow(ctx.user_id, "await_risk")
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "🛡 Настройка Risk на сделку\n"
            f"Сейчас: {profile.risk_per_trade_pct}%\n"
            "Введи число (например: 0.5 или 1.0):"
        )
        reply = (("⬅️ Назад", "🏠 Меню"),)
        return {"text": text, "reply_keyboard": reply}

    def risk_rr_handler(ctx: CommandContext, __: str) -> dict:
        _set_flow(ctx.user_id, "await_rr")
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "🎯 Настройка Risk/Reward\n"
            f"Сейчас: {profile.rr_ratio}\n"
            "Введи число (например: 2.0 или 2.5):"
        )
        reply = (("⬅️ Назад", "🏠 Меню"),)
        return {"text": text, "reply_keyboard": reply}

    def risk_dd_handler(ctx: CommandContext, __: str) -> dict:
        _set_flow(ctx.user_id, "await_dd")
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "🚫 Настройка дневной просадки (DD)\n"
            f"Сейчас: {profile.max_daily_drawdown_pct}%\n"
            "Введи число (например: 10 или 20):"
        )
        reply = (("⬅️ Назад", "🏠 Меню"),)
        return {"text": text, "reply_keyboard": reply}

    def risk_limits_handler(ctx: CommandContext, __: str) -> dict:
        _set_flow(ctx.user_id, "await_maxpos")
        text = "📦 Введи лимит открытых позиций (например: 1 или 3):"
        reply = (("⬅️ Назад", "🏠 Меню"),)
        return {"text": text, "reply_keyboard": reply}

    def risk_sl_handler(ctx: CommandContext, __: str) -> dict:
        _set_flow(ctx.user_id, "await_sl")
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "🧯 Настройка Stop Loss\n"
            f"Сейчас: {profile.sl_pct}%\n"
            "Введи число (например: 0.5):"
        )
        reply = (("⬅️ Назад", "🏠 Меню"),)
        return {"text": text, "reply_keyboard": reply}

    def risk_tp_handler(ctx: CommandContext, __: str) -> dict:
        _set_flow(ctx.user_id, "await_tp")
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "💰 Настройка Take Profit\n"
            f"Сейчас: {profile.tp_pct}%\n"
            "Введи число (например: 1.0):"
        )
        reply = (("⬅️ Назад", "🏠 Меню"),)
        return {"text": text, "reply_keyboard": reply}

    def menu_handler(ctx: CommandContext, __: str) -> dict:
        _clear_flow(ctx.user_id)
        return {
            "text": (
                "🏠 Главное меню\n"
                "Выбери раздел кнопками под строкой ввода.\n"
                "Все кнопки безопасны: они только меняют настройки профиля."
            ),
            "reply_keyboard": _main_menu_reply(),
        }

    def tf_menu_handler(ctx: CommandContext, __: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "⏱ Выбор таймфрейма\n"
            f"Сейчас: {profile.timeframe}\n"
            "1м — очень частые сигналы\n"
            "5м/15м — сбалансированный режим\n"
            "1ч/4ч — более спокойные сигналы"
        )
        inline = (
            (("⚡ 1м", "/set_tf 1m"), ("🚀 5м", "/set_tf 5m"), ("📘 15м", "/set_tf 15m")),
            (("🕐 1ч", "/set_tf 1h"), ("🌙 4ч", "/set_tf 4h")),
            (("🏠 Главное меню", "/menu"),),
        )
        return {"text": text, "inline_keyboard": inline, "reply_keyboard": _tf_menu_reply()}

    def mode_menu_handler(ctx: CommandContext, __: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "🤖 **Настройка режима работы**\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"Текущий статус: **{profile.mode}**\n\n"
            "🔔 **Signal Only**\n"
            "Только уведомления о сигналах. Торговля отключена.\n\n"
            "🧪 **Paper Trading**\n"
            "Симуляция торговли на виртуальном счете. Идеально для тестов.\n\n"
            "🔥 **Live Trading**\n"
            "Реальная торговля на бирже. Используются ваши средства!\n\n"
            "👇 Выбери режим кнопками внизу:"
        )
        return {"text": text, "reply_keyboard": _mode_menu_reply()}

    def backtest_handler(ctx: CommandContext, args: str) -> dict:
        symbol = ""
        timeframe = ""
        for token in args.split():
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            normalized_key = key.strip().lower()
            normalized_value = value.strip().upper() if normalized_key == "symbol" else value.strip().lower()
            if normalized_key == "symbol":
                symbol = normalized_value
            elif normalized_key in {"tf", "timeframe"}:
                timeframe = normalized_value
        
        if not symbol or not timeframe:
            _set_flow(ctx.user_id, "await_backtest")
            text = (
                "🧪 **Mini-Backtest**\n"
                "━━━━━━━━━━━━━━━━\n"
                "Быстрая проверка стратегии на истории.\n"
                "Бот загрузит свечи, прогонит ML-модель и покажет результат.\n\n"
                "👇 **Выбери пару из списка или напиши свою**\n"
                "Формат: `SYMBOL TIMEFRAME`\n"
                "Пример: `DOGEUSDT 15m`"
            )
            return {"text": text, "reply_keyboard": _backtest_menu_reply()}

        errors: list[str] = []
        if timeframe not in BACKTEST_TIMEFRAMES:
            errors.append("timeframe должен быть 1m|5m|15m|1h")
        if errors:
            return {"text": "Ошибка: " + "; ".join(errors)}

        local_candles = load_local_backtest_candles(symbol=symbol, timeframe=timeframe, limit=3000)
        candles = load_backtest_candles(symbol=symbol, timeframe=timeframe, limit=3000)
        
        if not candles:
            return {"text": f"❌ Не удалось загрузить данные для {symbol} {timeframe}"}

        backtest_report = run_mini_backtest(candles=candles, ml_filter=MlSignalFilter())
        fetch_status = "ok" if len(candles) >= 3000 else "partial"
        
        text = MiniBacktestReporter().build_report(
            symbol=symbol,
            timeframe=timeframe,
            candles_local_before=len(local_candles),
            candles_loaded=len(candles),
            remote_fetch=fetch_status,
            report=backtest_report,
        )
        # Clear flow after successful backtest
        _clear_flow(ctx.user_id)
        return {"text": text, "reply_keyboard": _backtest_menu_reply()}

    router.add_route("/start", start_handler)
    router.add_route("/help", help_handler)
    router.add_route("/hide_menu", hide_menu_handler)
    router.add_route("/mode", mode_handler)
    router.add_route("/pairs", pairs_handler)
    router.add_route("/pair_add", pair_add_handler)
    router.add_route("/pair_remove", pair_remove_handler)
    router.add_route("/pair_delete", pair_delete_handler)
    router.add_route("/text", text_handler)
    router.add_route("/set_tf", set_tf_handler)
    router.add_route("/set_risk", set_risk_handler)
    router.add_route("/set_rr", set_rr_handler)
    router.add_route("/set_dd", set_dd_handler)
    router.add_route("/set_maxpos", set_maxpos_handler)
    router.add_route("/set_sl", set_sl_handler)
    router.add_route("/set_tp", set_tp_handler)
    router.add_route("/close", close_handler)
    router.add_route("/status", status_handler)
    router.add_route("/menu", menu_handler)
    router.add_route("/tf_menu", tf_menu_handler)
    router.add_route("/mode_menu", mode_menu_handler)
    router.add_route("/positions", positions_handler)
    router.add_route("/ml_report", ml_report_handler)
    router.add_route("/ml_train", ml_train_handler)
    router.add_route("/news", news_handler)
    router.add_route("/readiness", readiness_handler)
    router.add_route("/risk", risk_menu_handler)
    router.add_route("/risk_risk", risk_risk_handler)
    router.add_route("/risk_rr", risk_rr_handler)
    router.add_route("/risk_dd", risk_dd_handler)
    router.add_route("/risk_limits", risk_limits_handler)
    router.add_route("/risk_sl", risk_sl_handler)
    router.add_route("/risk_tp", risk_tp_handler)
    router.add_route("/backtest", backtest_handler)
    return router


def _apply_start_updates(
    profile: TelegramUserProfile,
    args: str,
) -> tuple[TelegramUserProfile, list[str]]:
    values = {
        "mode": profile.mode,
        "exchange": profile.exchange,
        "timeframe": profile.timeframe,
        "risk": str(profile.risk_per_trade_pct),
        "rr": str(profile.rr_ratio),
        "dd": str(profile.max_daily_drawdown_pct),
        "maxpos": str(profile.max_open_positions),
        "sl": str(profile.sl_pct),
        "tp": str(profile.tp_pct),
        "report": str(profile.position_report_minutes),
    }
    errors: list[str] = []
    for token in args.split():
        if "=" not in token:
            errors.append(f"Неверный параметр: {token}")
            continue
        key, raw_value = token.split("=", 1)
        normalized_key = key.strip().lower()
        if normalized_key not in values:
            errors.append(f"Неизвестный параметр: {normalized_key}")
            continue
        values[normalized_key] = raw_value.strip()
    if errors:
        return profile, errors
    mode = _parse_mode(values["mode"], errors)
    exchange = values["exchange"].lower()
    timeframe = _parse_timeframe(values["timeframe"], errors)
    if exchange not in {"hyperliquid", "mexc"}:
        errors.append("exchange должен быть hyperliquid|mexc")
    risk_value = _parse_risk(values["risk"], errors)
    rr_value = _parse_rr(values["rr"], errors)
    dd_value = _parse_max_daily_drawdown(values["dd"], errors)
    max_pos_value = _parse_max_open_positions(values["maxpos"], errors)
    sl_value = _parse_sl_pct(values["sl"], errors)
    tp_value = _parse_tp_pct(values["tp"], errors)
    report_value = _parse_report_minutes(values["report"], errors)
    if errors:
        return profile, errors
    return (
        TelegramUserProfile(
            user_id=profile.user_id,
            mode=mode,
            exchange=exchange,
            timeframe=timeframe,
            risk_per_trade_pct=risk_value,
            rr_ratio=rr_value,
            max_daily_drawdown_pct=dd_value,
            max_open_positions=max_pos_value,
            sl_pct=sl_value,
            tp_pct=tp_value,
            open_positions_count=profile.open_positions_count,
            position_report_minutes=report_value,
            trading_pairs=profile.trading_pairs,
        ),
        [],
    )


def _main_menu_reply() -> tuple[tuple[str, ...], ...]:
    return (
        ("📊 Статус", "📍 Позиции", "🧩 Пары"),
        ("🛡 Риск", "🤖 Режим", "🧪 Backtest"),
        ("🧠 ML отчет", "📰 News", "🧭 Readiness"),
        ("🙈 Скрыть меню",),
    )


def _mode_menu_reply() -> tuple[tuple[str, ...], ...]:
    return (
        ("🔔 Только сигналы", "🧪 Paper", "🔥 Live"),
        ("🏠 Меню",),
    )


def _risk_menu_reply() -> tuple[tuple[str, ...], ...]:
    return (
        ("🛡 Настроить Risk", "🎯 Настроить RR"),
        ("🚫 Настроить DD", "📦 Лимит позиций"),
        ("🧯 SL", "💰 TP"),
        ("❌ Закрыть позицию", "🏠 Меню"),
    )


def _tf_menu_reply() -> tuple[tuple[str, ...], ...]:
    return (
        ("⚡ TF 1m", "🚀 TF 5m", "📘 TF 15m"),
        ("🕐 TF 1h", "🌙 TF 4h", "🏠 Меню"),
    )


def _pairs_menu_reply() -> tuple[tuple[str, ...], ...]:
    return (
        ("➕ Добавить пару", "➖ Удалить пару"),
        ("🏠 Меню",),
    )


def _backtest_menu_reply() -> tuple[tuple[str, ...], ...]:
    return (
        ("BTCUSDT 5m", "ETHUSDT 5m", "SOLUSDT 5m"),
        ("BTCUSDT 1h", "ETHUSDT 1h", "SOLUSDT 1h"),
        ("🏠 Меню",),
    )


def _is_secret_configured(value: str) -> bool:
    normalized = value.strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    if lowered.startswith("put_") and lowered.endswith("_here"):
        return False
    return True


def _parse_mode(raw: str, errors: list[str]) -> str:
    value = raw.strip().lower()
    if value not in {"signal_only", "paper", "live"}:
        errors.append("mode должен быть signal_only|paper|live")
    return value


def _parse_timeframe(raw: str, errors: list[str]) -> str:
    value = raw.strip().lower()
    if value not in {"1m", "5m", "15m", "1h", "4h"}:
        errors.append("timeframe должен быть 1m|5m|15m|1h|4h")
    return value


def _parse_pair_args(args: str) -> tuple[str, str, list[str]]:
    errors: list[str] = []
    symbol = ""
    timeframe = ""
    tokens = args.split()
    if len(tokens) >= 1:
        symbol = tokens[0].strip().upper()
    if len(tokens) >= 2:
        timeframe = tokens[1].strip().lower()
    if not symbol:
        errors.append("symbol обязателен, пример: BTCUSDT 5m")
    # Removed strict check against BACKTEST_SYMBOLS to allow any pair
    if not timeframe:
        errors.append("timeframe обязателен, пример: BTCUSDT 5m")
    elif timeframe not in {"1m", "5m", "15m", "1h", "4h"}:
        errors.append("timeframe должен быть 1m|5m|15m|1h|4h")
    return symbol, timeframe, errors


def _parse_risk(raw: str, errors: list[str]) -> float:
    try:
        value = float(raw)
    except ValueError:
        errors.append("risk должен быть числом")
        return 0.0
    check = RISK_MANAGER.validate_risk_per_trade_pct(value)
    if not check.allowed:
        errors.append(check.reason)
    return value


def _parse_rr(raw: str, errors: list[str]) -> float:
    try:
        value = float(raw)
    except ValueError:
        errors.append("rr должен быть числом")
        return 0.0
    if value < 1.0 or value > 5.0:
        errors.append("rr должен быть в диапазоне 1.0..5.0")
    return value


def _parse_max_daily_drawdown(raw: str, errors: list[str]) -> float:
    try:
        value = float(raw)
    except ValueError:
        errors.append("dd должен быть числом")
        return 0.0
    if value <= 0 or value > 60:
        errors.append("dd должен быть в диапазоне 1..60")
    return value


def _parse_max_open_positions(raw: str, errors: list[str]) -> int:
    try:
        value = int(raw)
    except ValueError:
        errors.append("maxpos должен быть целым числом")
        return 0
    if value < 1 or value > 10:
        errors.append("maxpos должен быть в диапазоне 1..10")
    return value


def _parse_sl_pct(raw: str, errors: list[str]) -> float:
    try:
        value = float(raw)
    except ValueError:
        errors.append("sl должен быть числом")
        return 0.0
    if value < 0.1 or value > 20:
        errors.append("sl должен быть в диапазоне 0.1..20")
    return value


def _parse_tp_pct(raw: str, errors: list[str]) -> float:
    try:
        value = float(raw)
    except ValueError:
        errors.append("tp должен быть числом")
        return 0.0
    if value < 0.1 or value > 50:
        errors.append("tp должен быть в диапазоне 0.1..50")
    return value


def _access_write_allowed(config: EnvironmentConfig) -> bool:
    return config.bot.access_mode.strip().lower() == "full_access"


def _parse_report_minutes(raw: str, errors: list[str]) -> int:
    try:
        value = int(raw)
    except ValueError:
        errors.append("report должен быть целым числом")
        return 0
    if value < 5 or value > 1440:
        errors.append("report должен быть в диапазоне 5..1440")
    return value


def _format_profile_error(profile: TelegramUserProfile, errors: list[str]) -> str:
    joined = "; ".join(errors)
    return (
        f"Ошибка обновления профиля: {joined}\n"
        f"Текущий профиль: mode={profile.mode} exchange={profile.exchange} "
        f"timeframe={profile.timeframe} risk={profile.risk_per_trade_pct} "
        f"rr={profile.rr_ratio} max_dd={profile.max_daily_drawdown_pct} "
        f"max_pos={profile.max_open_positions} "
        f"sl={profile.sl_pct} tp={profile.tp_pct} open_pos={profile.open_positions_count} "
        f"report={profile.position_report_minutes}"
    )
