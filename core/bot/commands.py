from dataclasses import replace

from core.bot.router import CommandContext
from core.bot.router import CommandRouter
from core.bot.profile import TelegramUserProfile
from core.bot.profile import TelegramUserProfileStore
from core.config.models import EnvironmentConfig
from core.ml.artifacts import ModelArtifactStore
from core.bot.reporter import MlQualityReporter
from core.bot.reporter import PositionReporter
from core.risk import RiskManager


COMMAND_KEYBOARD: tuple[tuple[str, ...], ...] = (
    ("/start", "/status", "/help"),
    ("/mode signal_only", "/mode paper", "/mode live"),
    ("/set_tf 1m", "/set_tf 5m", "/set_tf 15m"),
    ("/set_tf 1h", "/set_tf 4h"),
    ("/set_risk 0.5", "/set_risk 1.0", "/set_risk 1.5"),
    ("/positions", "/ml_report"),
)
RISK_MANAGER = RiskManager()


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
            f"report={profile.position_report_minutes}\n"
            "Для изменения профиля: /start mode=<signal_only|paper|live> "
            "exchange=<hyperliquid|mexc> timeframe=<1m|5m|15m|1h|4h> risk=<0.1..2.0> report=<5..1440>"
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

    def status_handler(ctx: CommandContext, __: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        return (
            "Статус каркаса Telegram Core: online\n"
            f"access_mode={config.bot.access_mode}\n"
            f"mode={profile.mode}\n"
            f"exchange={profile.exchange}\n"
            f"timeframe={profile.timeframe}\n"
            f"risk={profile.risk_per_trade_pct}\n"
            f"report_interval_min={profile.position_report_minutes}"
        )

    def positions_handler(ctx: CommandContext, __: str) -> dict:
        profile = store.get_or_create(ctx.user_id, config)
        text = PositionReporter().build_report(profile)
        inline = ((( "Обновить", "/positions"),),)
        return {"text": text, "inline_keyboard": inline}

    def ml_report_handler(_: CommandContext, __: str) -> str:
        return ml_reporter.build_report()

    router.add_route("/start", start_handler)
    router.add_route("/help", help_handler)
    router.add_route("/mode", mode_handler)
    router.add_route("/set_tf", set_tf_handler)
    router.add_route("/set_risk", set_risk_handler)
    router.add_route("/status", status_handler)
    router.add_route("/positions", positions_handler)
    router.add_route("/ml_report", ml_report_handler)
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
        f"report={profile.position_report_minutes}"
    )
