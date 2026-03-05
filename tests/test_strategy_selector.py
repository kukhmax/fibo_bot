import unittest

from core.strategies import select_strategy_by_regime


class TestStrategySelector(unittest.TestCase):
    def test_volatile_maps_to_breakout(self) -> None:
        self.assertEqual(select_strategy_by_regime("volatile"), "volatility_breakout")

    def test_trend_maps_to_trend_pullback(self) -> None:
        self.assertEqual(select_strategy_by_regime("trend_up"), "trend_pullback")
        self.assertEqual(select_strategy_by_regime("trend_down"), "trend_pullback")

    def test_range_maps_to_liquidity_sweep(self) -> None:
        self.assertEqual(select_strategy_by_regime("range"), "liquidity_sweep")

    def test_unknown_uses_fallback(self) -> None:
        self.assertEqual(select_strategy_by_regime("unknown", fallback="trend_pullback"), "trend_pullback")


if __name__ == "__main__":
    unittest.main()
