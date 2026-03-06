from datetime import datetime
from datetime import timezone
from pathlib import Path
import tempfile
import unittest

from core.bot.alerts import RiskAlertNotifier
from core.data import StateCache


class _TransportStub:
    def __init__(self) -> None:
        self.sent_messages: list[tuple[int, str]] = []

    def send_text(self, chat_id: int, text: str, reply_keyboard=None, inline_keyboard=None) -> None:
        self.sent_messages.append((chat_id, text))


class TestRiskAlerts(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._cache = StateCache(Path(self._tmp.name) / "risk_alert_state.json")
        self._transport = _TransportStub()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_sends_alert_on_first_call(self) -> None:
        notifier = RiskAlertNotifier(cooldown_minutes=30, state_cache=self._cache)
        sent = notifier.maybe_send(
            transport=self._transport,
            chat_id=11,
            user_id=22,
            code="DAILY_DRAWDOWN_BLOCK",
            details="daily_drawdown=11.0% limit=10.0%",
            now_utc=datetime(2026, 3, 6, 10, 0, tzinfo=timezone.utc),
        )
        self.assertTrue(sent)
        self.assertEqual(len(self._transport.sent_messages), 1)
        self.assertIn("КРИТИЧЕСКИЙ РИСК-АЛЕРТ", self._transport.sent_messages[0][1])

    def test_suppresses_repeated_alerts_within_cooldown(self) -> None:
        notifier = RiskAlertNotifier(cooldown_minutes=30, state_cache=self._cache)
        first_time = datetime(2026, 3, 6, 10, 0, tzinfo=timezone.utc)
        second_time = datetime(2026, 3, 6, 10, 10, tzinfo=timezone.utc)
        notifier.maybe_send(
            transport=self._transport,
            chat_id=11,
            user_id=22,
            code="MAX_OPEN_POSITIONS_BLOCK",
            details="open_positions=2 limit=2",
            now_utc=first_time,
        )
        sent_again = notifier.maybe_send(
            transport=self._transport,
            chat_id=11,
            user_id=22,
            code="MAX_OPEN_POSITIONS_BLOCK",
            details="open_positions=2 limit=2",
            now_utc=second_time,
        )
        self.assertFalse(sent_again)
        self.assertEqual(len(self._transport.sent_messages), 1)

    def test_allows_alert_after_cooldown(self) -> None:
        notifier = RiskAlertNotifier(cooldown_minutes=30, state_cache=self._cache)
        first_time = datetime(2026, 3, 6, 10, 0, tzinfo=timezone.utc)
        after_cooldown = datetime(2026, 3, 6, 10, 31, tzinfo=timezone.utc)
        notifier.maybe_send(
            transport=self._transport,
            chat_id=11,
            user_id=22,
            code="RISK_PER_TRADE_BLOCK",
            details="risk=3.0 reason=range",
            now_utc=first_time,
        )
        sent_again = notifier.maybe_send(
            transport=self._transport,
            chat_id=11,
            user_id=22,
            code="RISK_PER_TRADE_BLOCK",
            details="risk=3.0 reason=range",
            now_utc=after_cooldown,
        )
        self.assertTrue(sent_again)
        self.assertEqual(len(self._transport.sent_messages), 2)


if __name__ == "__main__":
    unittest.main()
