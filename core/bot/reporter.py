from datetime import datetime, timezone

from core.bot.profile import TelegramUserProfile


class PositionReporter:
    def build_report(self, profile: TelegramUserProfile) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return (
            "Отчет по позициям\n"
            f"mode={profile.mode} exchange={profile.exchange} timeframe={profile.timeframe}\n"
            "Нет открытых позиций\n"
            f"ts={now}"
        )
