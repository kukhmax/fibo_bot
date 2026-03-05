import unittest

from core.risk import RiskManager


class TestRiskManager(unittest.TestCase):
    def test_validate_risk_allows_within_limit(self) -> None:
        manager = RiskManager()
        result = manager.validate_risk_per_trade_pct(2.0)
        self.assertTrue(result.allowed)
        self.assertEqual(result.risk_per_trade_pct, 2.0)

    def test_validate_risk_blocks_over_limit(self) -> None:
        manager = RiskManager()
        result = manager.validate_risk_per_trade_pct(2.01)
        self.assertFalse(result.allowed)
        self.assertIn("0.1..2.0", result.reason)

    def test_calc_risk_amount(self) -> None:
        manager = RiskManager()
        self.assertEqual(manager.calc_risk_amount(1000.0, 1.0), 10.0)
        self.assertEqual(manager.calc_risk_amount(1000.0, 2.5), 0.0)

    def test_calc_position_size(self) -> None:
        manager = RiskManager()
        self.assertEqual(manager.calc_position_size(100.0, 99.0, 10.0), 10.0)
        self.assertEqual(manager.calc_position_size(100.0, 100.0, 10.0), 0.0)


if __name__ == "__main__":
    unittest.main()
