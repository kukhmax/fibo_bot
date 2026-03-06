from dataclasses import replace

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
from core.risk import RiskManager


COMMAND_KEYBOARD: tuple[tuple[str, ...], ...] = (
    ("/start", "/status", "/help"),
    ("/mode signal_only", "/mode paper", "/mode live"),
    ("/set_tf 1m", "/set_tf 5m", "/set_tf 15m"),
    ("/set_tf 1h", "/set_tf 4h"),
    ("/set_risk 0.5", "/set_risk 1.0", "/set_risk 1.5"),
    ("/set_rr 1.5", "/set_rr 2.0"),
    ("/set_dd 5", "/set_dd 10"),
    ("/set_maxpos 1", "/set_maxpos 2", "/set_maxpos 3"),
    ("/set_sl 0.5", "/set_tp 1.0", "/close"),
    ("/positions", "/ml_report", "/risk"),
    ("/backtest",),
)
RISK_MANAGER = RiskManager()
BACKTEST_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
BACKTEST_TIMEFRAMES: tuple[str, ...] = ("1m", "5m", "15m", "1h")


def build_default_router(
    config: EnvironmentConfig,
    profile_store: TelegramUserProfileStore | None = None,
    ml_artifact_store: ModelArtifactStore | None = None,
) -> CommandRouter:
    router = CommandRouter()
    store = profile_store or TelegramUserProfileStore()
    ml_reporter = MlQualityReporter(artifact_store=ml_artifact_store)
    router.set_reply_keyboard(COMMAND_KEYBOARD)

    def start_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        if args.strip():
            if not _access_write_allowed(config):
                return (
                    "Режим доступа notify_only: изменение настроек запрещено.\n"
                    f"Текущий профиль: mode={profile.mode} exchange={profile.exchange} "
                    f"timeframe={profile.timeframe} risk={profile.risk_per_trade_pct} "
                    f"rr={profile.rr_ratio} max_dd={profile.max_daily_drawdown_pct} "
                    f"max_pos={profile.max_open_positions} "
                    f"sl={profile.sl_pct} tp={profile.tp_pct} open_pos={profile.open_positions_count} "
                    f"report={profile.position_report_minutes}"
                )
            updated, errors = _apply_start_updates(profile, args)
            if errors:
                return _format_profile_error(profile, errors)
            store.save(updated)
            profile = updated
        return (
            "fib_bot готов.\n"
            f"env={config.environment}\n"
            f"mode={profile.mode}\n"
            f"exchange={profile.exchange}\n"
            f"timeframe={profile.timeframe}\n"
            f"risk={profile.risk_per_trade_pct}\n"
            f"rr={profile.rr_ratio}\n"
            f"max_dd={profile.max_daily_drawdown_pct}\n"
            f"max_pos={profile.max_open_positions}\n"
            f"sl={profile.sl_pct}\n"
            f"tp={profile.tp_pct}\n"
            f"open_pos={profile.open_positions_count}\n"
            f"report={profile.position_report_minutes}\n"
            "Для изменения профиля: /start mode=<signal_only|paper|live> "
            "exchange=<hyperliquid|mexc> timeframe=<1m|5m|15m|1h|4h> risk=<0.1..2.0> rr=<1.0..5.0> dd=<1..10> maxpos=<1..10> sl=<0.1..20> tp=<0.1..50> report=<5..1440>"
        )

    def help_handler(_: CommandContext, __: str) -> str:
        commands = ", ".join(router.available_commands())
        return f"Доступные команды: {commands}\nКнопки снизу дублируют команды и настройки."

    def mode_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_mode = args.strip().lower()
        if not raw_mode:
            return f"Текущий mode={profile.mode}. Использование: /mode <signal_only|paper|live>"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        mode = _parse_mode(raw_mode, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, mode=mode)
        store.save(updated)
        return f"mode обновлен: {updated.mode}"

    def set_tf_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_timeframe = args.strip().lower()
        if not raw_timeframe:
            return f"Текущий timeframe={profile.timeframe}. Использование: /set_tf <1m|5m|15m|1h|4h>"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        timeframe = _parse_timeframe(raw_timeframe, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, timeframe=timeframe)
        store.save(updated)
        return f"timeframe обновлен: {updated.timeframe}"

    def set_risk_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_risk = args.strip()
        if not raw_risk:
            return f"Текущий risk={profile.risk_per_trade_pct}. Использование: /set_risk <0.1..2.0>"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        risk = _parse_risk(raw_risk, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, risk_per_trade_pct=risk)
        store.save(updated)
        return f"risk обновлен: {updated.risk_per_trade_pct}"

    def set_rr_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_rr = args.strip()
        if not raw_rr:
            return f"Текущий rr={profile.rr_ratio}. Использование: /set_rr <1.0..5.0>"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        rr = _parse_rr(raw_rr, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, rr_ratio=rr)
        store.save(updated)
        return f"rr обновлен: {updated.rr_ratio}"

    def set_dd_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_dd = args.strip()
        if not raw_dd:
            return f"Текущий max_dd={profile.max_daily_drawdown_pct}. Использование: /set_dd <1..10>"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        max_dd = _parse_max_daily_drawdown(raw_dd, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, max_daily_drawdown_pct=max_dd)
        store.save(updated)
        return f"max_dd обновлен: {updated.max_daily_drawdown_pct}"

    def set_maxpos_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_maxpos = args.strip()
        if not raw_maxpos:
            return f"Текущий max_pos={profile.max_open_positions}. Использование: /set_maxpos <1..10>"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        max_pos = _parse_max_open_positions(raw_maxpos, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, max_open_positions=max_pos)
        store.save(updated)
        return f"max_pos обновлен: {updated.max_open_positions}"

    def set_sl_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_sl = args.strip()
        if not raw_sl:
            return f"Текущий sl={profile.sl_pct}. Использование: /set_sl <0.1..20>"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        sl = _parse_sl_pct(raw_sl, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, sl_pct=sl)
        store.save(updated)
        return f"sl обновлен: {updated.sl_pct}"

    def set_tp_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        raw_tp = args.strip()
        if not raw_tp:
            return f"Текущий tp={profile.tp_pct}. Использование: /set_tp <0.1..50>"
        if not _access_write_allowed(config):
            return "Режим доступа notify_only: команда недоступна."
        errors: list[str] = []
        tp = _parse_tp_pct(raw_tp, errors)
        if errors:
            return _format_profile_error(profile, errors)
        updated = replace(profile, tp_pct=tp)
        store.save(updated)
        return f"tp обновлен: {updated.tp_pct}"

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
            "Статус каркаса Telegram Core: online\n"
            f"access_mode={config.bot.access_mode}\n"
            f"mode={profile.mode}\n"
            f"exchange={profile.exchange}\n"
            f"timeframe={profile.timeframe}\n"
            f"risk={profile.risk_per_trade_pct}\n"
            f"rr={profile.rr_ratio}\n"
            f"max_dd={profile.max_daily_drawdown_pct}\n"
            f"max_pos={profile.max_open_positions}\n"
            f"sl={profile.sl_pct}\n"
            f"tp={profile.tp_pct}\n"
            f"open_pos={profile.open_positions_count}\n"
            f"report_interval_min={profile.position_report_minutes}"
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
            "Risk меню\n"
            f"risk={profile.risk_per_trade_pct}\n"
            f"rr={profile.rr_ratio}\n"
            f"max_dd={profile.max_daily_drawdown_pct}\n"
            f"max_pos={profile.max_open_positions}\n"
            f"sl={profile.sl_pct}\n"
            f"tp={profile.tp_pct}\n"
            f"open_pos={profile.open_positions_count}\n"
            "Выбери быстрый пресет:"
        )
        inline = (
            (("Risk 0.5%", "/set_risk 0.5"), ("Risk 1.0%", "/set_risk 1.0"), ("Risk 1.5%", "/set_risk 1.5")),
            (("RR 1.5", "/set_rr 1.5"), ("RR 2.0", "/set_rr 2.0"), ("RR 2.5", "/set_rr 2.5")),
            (("DD 5%", "/set_dd 5"), ("DD 8%", "/set_dd 8"), ("DD 10%", "/set_dd 10")),
            (("MaxPos 1", "/set_maxpos 1"), ("MaxPos 2", "/set_maxpos 2"), ("MaxPos 3", "/set_maxpos 3")),
            (("SL 0.5%", "/set_sl 0.5"), ("TP 1.0%", "/set_tp 1.0"), ("Close 1", "/close")),
            (("Обновить", "/risk"),),
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
    router.add_route("/positions", positions_handler)
    router.add_route("/ml_report", ml_report_handler)
    router.add_route("/risk", risk_menu_handler)
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
