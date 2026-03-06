import unittest

from core.backtest import run_mini_backtest
from core.data import Candle


class _MlInferenceStub:
    def __init__(self, allow: bool) -> None:
        self.allow = allow
        self.probability = 0.9 if allow else 0.1
        self.reason = "stub"


class _MlFilterStub:
    def __init__(self, allow: bool) -> None:
        self._allow = allow

    def is_active(self) -> bool:
        return True

    def evaluate(self, candles: list[Candle]) -> _MlInferenceStub:
        return _MlInferenceStub(allow=self._allow)


class TestMiniBacktestRunner(unittest.TestCase):
    def _build_trend_candles(self, count: int = 40) -> list[Candle]:
        candles: list[Candle] = []
        for idx in range(count):
            open_time = idx * 60_000
            close_time = open_time + 59_999
            base = 100.0 + idx * 0.35
            candles.append(
                Candle(
                    symbol="BTCUSDT",
                    timeframe="5m",
                    open_time_ms=open_time,
                    close_time_ms=close_time,
                    open=base,
                    high=base + 0.5,
                    low=base - 0.3,
                    close=base + 0.2,
                    volume=100 + idx,
                )
            )
        return candles

    def test_runner_counts_entries_without_ml_filter(self) -> None:
        report = run_mini_backtest(candles=self._build_trend_candles(), ml_filter=None)
        self.assertGreater(report.entries_total, 0)
        self.assertEqual(report.entries_after_ml, report.entries_total)
        self.assertEqual(report.entries_blocked_ml, 0)
        self.assertGreater(report.trades, 0)
        self.assertGreaterEqual(report.winrate, 0.0)
        self.assertGreaterEqual(report.profit_factor, 0.0)
        self.assertGreaterEqual(report.max_drawdown_r, 0.0)
        self.assertGreaterEqual(report.avg_rr, 0.0)
        self.assertGreater(report.regime_counts.get("trend_up", 0), 0)

    def test_runner_blocks_entries_when_ml_rejects(self) -> None:
        report = run_mini_backtest(candles=self._build_trend_candles(), ml_filter=_MlFilterStub(allow=False))
        self.assertGreater(report.entries_total, 0)
        self.assertEqual(report.entries_after_ml, 0)
        self.assertEqual(report.entries_blocked_ml, report.entries_total)
        self.assertEqual(report.trades, 0)


if __name__ == "__main__":
    unittest.main()
