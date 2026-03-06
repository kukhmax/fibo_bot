import unittest

from core.bot.news_engine import NewsRiskGate


class TestNewsEngine(unittest.TestCase):
    def test_blocks_headline_with_risk_keywords(self) -> None:
        gate = NewsRiskGate(
            source="t.me/cryptoarsenal",
            keywords=("hack", "bankruptcy", "liquidation"),
            min_block_score=1,
        )
        decision = gate.evaluate("Major exchange hack triggers liquidation wave")
        self.assertTrue(decision.blocked)
        self.assertIn("hack", decision.matched_keywords)

    def test_allows_headline_without_risk_keywords(self) -> None:
        gate = NewsRiskGate(
            source="t.me/cryptoarsenal",
            keywords=("hack", "bankruptcy", "liquidation"),
            min_block_score=1,
        )
        decision = gate.evaluate("ETF inflows increase for major assets")
        self.assertFalse(decision.blocked)
        self.assertEqual(decision.reason, "news_ok")


if __name__ == "__main__":
    unittest.main()
