from pathlib import Path
from datetime import datetime
from datetime import timezone
import tempfile
import unittest

from core.data.persistence import StateCache
from core.risk import DailyDrawdownGuard


class TestRiskDrawdown(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._cache = StateCache(Path(self._tmp.name) / "risk_state.json")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_allows_when_within_daily_limit(self) -> None:
        guard = DailyDrawdownGuard(max_daily_drawdown_pct=10.0, state_cache=self._cache)
        first = guard.evaluate(user_id=1, current_equity=1000.0)
        second = guard.evaluate(user_id=1, current_equity=930.0)
        self.assertTrue(first.allowed)
        self.assertTrue(second.allowed)
        self.assertAlmostEqual(second.drawdown_pct, 7.0)

    def test_blocks_when_daily_limit_exceeded(self) -> None:
        guard = DailyDrawdownGuard(max_daily_drawdown_pct=10.0, state_cache=self._cache)
        guard.evaluate(user_id=1, current_equity=1000.0)
        blocked = guard.evaluate(user_id=1, current_equity=890.0)
        self.assertFalse(blocked.allowed)
        self.assertIn("max_daily_drawdown_exceeded", blocked.reason)

    def test_pauses_until_next_utc_day_after_limit_exceeded(self) -> None:
        guard = DailyDrawdownGuard(max_daily_drawdown_pct=10.0, pause_until_utc_hour=0, state_cache=self._cache)
        day1 = datetime(2026, 3, 6, 10, 0, tzinfo=timezone.utc)
        day2 = datetime(2026, 3, 7, 0, 1, tzinfo=timezone.utc)
        guard.evaluate(user_id=1, current_equity=1000.0, now_utc=day1)
        first_block = guard.evaluate(user_id=1, current_equity=890.0, now_utc=day1)
        still_paused = guard.evaluate(user_id=1, current_equity=995.0, now_utc=day1)
        next_day = guard.evaluate(user_id=1, current_equity=995.0, now_utc=day2)
        self.assertFalse(first_block.allowed)
        self.assertIn("max_daily_drawdown_exceeded", first_block.reason)
        self.assertFalse(still_paused.allowed)
        self.assertIn("paused_until_utc_00", still_paused.reason)
        self.assertTrue(next_day.allowed)

    def test_invalid_equity_is_blocked(self) -> None:
        guard = DailyDrawdownGuard(max_daily_drawdown_pct=10.0, state_cache=self._cache)
        check = guard.evaluate(user_id=1, current_equity=0.0)
        self.assertFalse(check.allowed)
        self.assertEqual(check.reason, "invalid_equity")


if __name__ == "__main__":
    unittest.main()
