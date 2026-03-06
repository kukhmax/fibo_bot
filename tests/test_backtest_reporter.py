import unittest

from core.backtest import MiniBacktestRunReport
from core.bot.reporter import MiniBacktestReporter


class TestBacktestReporter(unittest.TestCase):
    def test_build_report_has_structured_sections(self) -> None:
        report = MiniBacktestRunReport(
            candles_count=3000,
            entries_total=120,
            entries_after_ml=90,
            entries_blocked_ml=30,
            trades=90,
            winrate=0.55,
            profit_factor=1.4,
            max_drawdown_r=3.2,
            avg_rr=1.1,
            expectancy_r=0.08,
            regime_counts={"trend_up": 1500, "range": 1200, "volatile": 300},
            strategy_entry_counts={"trend_pullback": 70, "liquidity_sweep": 20},
        )
        text = MiniBacktestReporter().build_report(
            symbol="BTCUSDT",
            timeframe="5m",
            candles_local_before=1800,
            candles_loaded=3000,
            remote_fetch="ok",
            report=report,
        )
        self.assertIn("Mini-backtest отчет", text)
        self.assertIn("[Параметры]", text)
        self.assertIn("[Сигналы]", text)
        self.assertIn("[Метрики]", text)
        self.assertIn("[Распределения]", text)
        self.assertIn("symbol=BTCUSDT", text)
        self.assertIn("pf=1.4000", text)


if __name__ == "__main__":
    unittest.main()
