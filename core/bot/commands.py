from core.bot.router import CommandContext
from core.bot.router import CommandRouter
from core.bot.profile import TelegramUserProfile
from core.bot.profile import TelegramUserProfileStore
from core.config.models import EnvironmentConfig


def build_default_router(
    config: EnvironmentConfig,
    profile_store: TelegramUserProfileStore | None = None,
) -> CommandRouter:
    router = CommandRouter()
    store = profile_store or TelegramUserProfileStore()

    def start_handler(ctx: CommandContext, args: str) -> str:
        profile = store.get_or_create(ctx.user_id, config)
        if args.strip():
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
        return f"Доступные команды: {commands}"

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

    router.add_route("/start", start_handler)
    router.add_route("/help", help_handler)
    router.add_route("/status", status_handler)
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
    mode = values["mode"].lower()
    exchange = values["exchange"].lower()
    timeframe = values["timeframe"].lower()
    if mode not in {"signal_only", "paper", "live"}:
        errors.append("mode должен быть signal_only|paper|live")
    if exchange not in {"hyperliquid", "mexc"}:
        errors.append("exchange должен быть hyperliquid|mexc")
    if timeframe not in {"1m", "5m", "15m", "1h", "4h"}:
        errors.append("timeframe должен быть 1m|5m|15m|1h|4h")
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


def _parse_risk(raw: str, errors: list[str]) -> float:
    try:
        value = float(raw)
    except ValueError:
        errors.append("risk должен быть числом")
        return 0.0
    if value <= 0 or value > 2:
        errors.append("risk должен быть в диапазоне 0.1..2.0")
    return value


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
