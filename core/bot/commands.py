from core.bot.router import CommandContext
from core.bot.router import CommandRouter
from core.config.models import EnvironmentConfig


def build_default_router(config: EnvironmentConfig) -> CommandRouter:
    router = CommandRouter()

    def start_handler(_: CommandContext, __: str) -> str:
        return (
            "fib_bot готов.\n"
            f"env={config.environment}\n"
            f"mode={config.bot.mode}\n"
            f"exchange={config.exchange.primary}\n"
            f"timeframe={config.exchange.default_timeframe}"
        )

    def help_handler(_: CommandContext, __: str) -> str:
        commands = ", ".join(router.available_commands())
        return f"Доступные команды: {commands}"

    def status_handler(_: CommandContext, __: str) -> str:
        return (
            "Статус каркаса Telegram Core: online\n"
            f"access_mode={config.bot.access_mode}\n"
            f"report_interval_min={config.bot.position_report_minutes}"
        )

    router.add_route("/start", start_handler)
    router.add_route("/help", help_handler)
    router.add_route("/status", status_handler)
    return router
