from dataclasses import dataclass


@dataclass(frozen=True)
class NewsRiskDecision:
    blocked: bool
    score: int
    matched_keywords: tuple[str, ...]
    reason: str


class NewsRiskGate:
    def __init__(self, source: str, keywords: tuple[str, ...], min_block_score: int = 1) -> None:
        self.source = source.strip()
        self.keywords = tuple(item.strip().lower() for item in keywords if item.strip())
        self.min_block_score = max(1, int(min_block_score))

    def evaluate(self, headline: str) -> NewsRiskDecision:
        text = headline.strip().lower()
        if not text:
            return NewsRiskDecision(blocked=False, score=0, matched_keywords=(), reason="headline_empty")
        matched = tuple(item for item in self.keywords if item in text)
        score = len(matched)
        if score >= self.min_block_score:
            return NewsRiskDecision(
                blocked=True,
                score=score,
                matched_keywords=matched,
                reason=f"news_risk:{'|'.join(matched)}",
            )
        return NewsRiskDecision(blocked=False, score=score, matched_keywords=matched, reason="news_ok")
