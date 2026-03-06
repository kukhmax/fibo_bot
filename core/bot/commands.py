from dataclasses import replace
import os

from core.bot.router import CommandContext
from core.bot.router import CommandRouter
from core.bot.profile import TelegramUserProfile
from core.bot.profile import TelegramUserProfileStore
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
from core.risk import RiskManager


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

    def start_handler(ctx: CommandContext, args: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        if args.strip():
            if not _access_write_allowed(config):
                return {"text": "🔒 Сейчас только режим уведомлений, менять настройки нельзя.", "inline_keyboard": _main_menu_inline()}
            updated, errors = _apply_start_updates(profile, args)
            if errors:
                return {"text": _format_profile_error(profile, errors), "inline_keyboard": _main_menu_inline()}
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
        return {"text": text, "inline_keyboard": _main_menu_inline()}

    def help_handler(_: CommandContext, __: str) -> str:
        return (
            "❓ Как пользоваться ботом\n"
            "1) Нажми /start — увидишь главное меню\n"
            "2) Выбери ⏱ Таймфрейм и 🛡 Риск\n"
            "3) Настрой 🎯 RR, 🚫 DD и 📦 лимит позиций в меню риска\n"
            "4) Проверь профиль через 📊 Статус\n"
            "5) Запусти 🧪 Mini-backtest для проверки актива\n\n"
            "Команды для быстрого доступа:\n"
            "/menu /status /risk /tf_menu /mode_menu /backtest /positions /ml_report /readiness /hide_menu"
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
            f"📍 Открытых позиций: {profile.open_positions_count}\n"
            f"🔔 Интервал отчета: {profile.position_report_minutes} мин"
        )

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

    def ml_report_handler(_: CommandContext, __: str) -> str:
        return ml_reporter.build_report()

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
        inline = (
            (("🛡 Настроить Risk", "/risk_risk"), ("🎯 Настроить RR", "/risk_rr")),
            (("🚫 Настроить DD", "/risk_dd"), ("📦 Лимит позиций", "/risk_limits")),
            (("🧯 SL/TP", "/risk_sl_tp"), ("❌ Закрыть позицию", "/close")),
            (("🔄 Обновить", "/risk"), ("🏠 Главное меню", "/menu")),
        )
        return {"text": text, "inline_keyboard": inline}

    def risk_risk_handler(ctx: CommandContext, __: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "🛡 Настройка Risk на сделку\n"
            f"Сейчас: {profile.risk_per_trade_pct}%\n"
            "Рекомендация: 0.5% - 1.0% для спокойного режима."
        )
        inline = (
            (("🛡 0.5%", "/set_risk 0.5"), ("🛡 1.0%", "/set_risk 1.0"), ("🛡 1.5%", "/set_risk 1.5")),
            (("⬅️ Назад в риск-меню", "/risk"), ("🏠 Главное меню", "/menu")),
        )
        return {"text": text, "inline_keyboard": inline}

    def risk_rr_handler(ctx: CommandContext, __: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "🎯 Настройка Risk/Reward\n"
            f"Сейчас: {profile.rr_ratio}\n"
            "Чем выше RR, тем реже исполнение, но выше цель."
        )
        inline = (
            (("🎯 1.5", "/set_rr 1.5"), ("🎯 2.0", "/set_rr 2.0"), ("🎯 2.5", "/set_rr 2.5")),
            (("⬅️ Назад в риск-меню", "/risk"), ("🏠 Главное меню", "/menu")),
        )
        return {"text": text, "inline_keyboard": inline}

    def risk_dd_handler(ctx: CommandContext, __: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "🚫 Настройка дневной просадки (DD)\n"
            f"Сейчас: {profile.max_daily_drawdown_pct}%\n"
            "При превышении лимита новые входы блокируются до следующего UTC-дня."
        )
        inline = (
            (("🚫 5%", "/set_dd 5"), ("🚫 8%", "/set_dd 8"), ("🚫 10%", "/set_dd 10")),
            (("⬅️ Назад в риск-меню", "/risk"), ("🏠 Главное меню", "/menu")),
        )
        return {"text": text, "inline_keyboard": inline}

    def risk_limits_handler(_: CommandContext, __: str) -> dict:
        text = "📦 Лимит открытых позиций"
        inline = (
            (("📦 1", "/set_maxpos 1"), ("📦 2", "/set_maxpos 2"), ("📦 3", "/set_maxpos 3")),
            (("⬅️ Назад в риск-меню", "/risk"), ("🏠 Главное меню", "/menu")),
        )
        return {"text": text, "inline_keyboard": inline}

    def risk_sl_tp_handler(ctx: CommandContext, __: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "🧯 Настройка SL/TP\n"
            f"Сейчас SL: {profile.sl_pct}%\n"
            f"Сейчас TP: {profile.tp_pct}%"
        )
        inline = (
            (("🧯 SL 0.5%", "/set_sl 0.5"), ("🧯 SL 1.0%", "/set_sl 1.0")),
            (("💰 TP 1.0%", "/set_tp 1.0"), ("💰 TP 2.0%", "/set_tp 2.0")),
            (("⬅️ Назад в риск-меню", "/risk"), ("🏠 Главное меню", "/menu")),
        )
        return {"text": text, "inline_keyboard": inline}

    def menu_handler(_: CommandContext, __: str) -> dict:
        return {
            "text": (
                "🏠 Главное меню\n"
                "Выбери раздел. Все кнопки безопасны: они только меняют настройки профиля."
            ),
            "inline_keyboard": _main_menu_inline(),
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
        return {"text": text, "inline_keyboard": inline}

    def mode_menu_handler(ctx: CommandContext, __: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        text = (
            "🤖 Выбор режима\n"
            f"Сейчас: {profile.mode}\n"
            "signal_only — только сигналы\n"
            "paper — тест без реальных денег\n"
            "live — боевой режим"
        )
        inline = (
            (("🔔 Только сигналы", "/mode signal_only"), ("🧪 Paper", "/mode paper"), ("🔥 Live", "/mode live")),
            (("🏠 Главное меню", "/menu"),),
        )
        return {"text": text, "inline_keyboard": inline}

    def backtest_handler(_: CommandContext, args: str) -> dict:
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
            text = (
                "Mini-backtest\n"
                "Шаг 1/4: выбери актив и таймфрейм.\n"
                "Использование: /backtest symbol=<BTCUSDT|ETHUSDT|SOLUSDT> timeframe=<1m|5m|15m|1h>"
            )
            inline = (
                (("BTC 5m", "/backtest symbol=BTCUSDT timeframe=5m"), ("ETH 5m", "/backtest symbol=ETHUSDT timeframe=5m")),
                (("SOL 5m", "/backtest symbol=SOLUSDT timeframe=5m"), ("BTC 1h", "/backtest symbol=BTCUSDT timeframe=1h")),
                (("ETH 15m", "/backtest symbol=ETHUSDT timeframe=15m"), ("SOL 1m", "/backtest symbol=SOLUSDT timeframe=1m")),
            )
            return {"text": text, "inline_keyboard": inline}
        errors: list[str] = []
        if symbol not in BACKTEST_SYMBOLS:
            errors.append("symbol должен быть BTCUSDT|ETHUSDT|SOLUSDT")
        if timeframe not in BACKTEST_TIMEFRAMES:
            errors.append("timeframe должен быть 1m|5m|15m|1h")
        if errors:
            text = "Ошибка mini-backtest: " + "; ".join(errors)
            return {"text": text, "inline_keyboard": None}
        local_candles = load_local_backtest_candles(symbol=symbol, timeframe=timeframe, limit=3000)
        candles = load_backtest_candles(symbol=symbol, timeframe=timeframe, limit=3000)
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
        inline = ((( "Изменить выбор", "/backtest"),),)
        return {"text": text, "inline_keyboard": inline}

    router.add_route("/start", start_handler)
    router.add_route("/help", help_handler)
    router.add_route("/hide_menu", hide_menu_handler)
    router.add_route("/mode", mode_handler)
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
    router.add_route("/news", news_handler)
    router.add_route("/readiness", readiness_handler)
    router.add_route("/risk", risk_menu_handler)
    router.add_route("/risk_risk", risk_risk_handler)
    router.add_route("/risk_rr", risk_rr_handler)
    router.add_route("/risk_dd", risk_dd_handler)
    router.add_route("/risk_limits", risk_limits_handler)
    router.add_route("/risk_sl_tp", risk_sl_tp_handler)
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
        ),
        [],
    )


def _main_menu_inline() -> tuple[tuple[tuple[str, str], ...], ...]:
    return (
        (("📊 Статус", "/status"), ("📍 Позиции", "/positions")),
        (("⏱ Таймфрейм", "/tf_menu"), ("🛡 Риск и RR", "/risk")),
        (("🤖 Режим", "/mode_menu"), ("🧪 Mini-backtest", "/backtest")),
        (("🧠 ML отчет", "/ml_report"), ("📰 News", "/news")),
        (("🧭 Live readiness", "/readiness"), ("❓ Помощь", "/help")),
    )


def _main_menu_reply() -> tuple[tuple[str, ...], ...]:
    return (
        ("📊 Статус", "📍 Позиции", "🏠 Меню"),
        ("⏱ Таймфрейм", "🛡 Риск", "🤖 Режим"),
        ("🧪 Backtest", "🧠 ML отчет", "📰 News"),
        ("🧭 Readiness", "🙈 Скрыть меню"),
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
    if value <= 0 or value > 10:
        errors.append("dd должен быть в диапазоне 1..10")
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
