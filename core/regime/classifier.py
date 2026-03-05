from dataclasses import dataclass

from core.data.models import Candle


@dataclass(frozen=True)
class RegimeClassification:
    label: str
    confidence: float
    explanation: str


class RuleBasedRegimeClassifier:
    def classify(self, candles: list[Candle]) -> RegimeClassification:
        if len(candles) < 5:
            return RegimeClassification(
                label="unknown",
                confidence=0.0,
                explanation="not enough candles",
            )
        ordered = sorted(candles, key=lambda c: c.open_time_ms)
        closes = [item.close for item in ordered]
        highs = [item.high for item in ordered]
        lows = [item.low for item in ordered]
        opens = [item.open for item in ordered]
        trend_move = (closes[-1] - closes[0]) / max(abs(closes[0]), 1e-9)
        step_vol = []
        for idx in range(1, len(closes)):
            prev = max(abs(closes[idx - 1]), 1e-9)
            step_vol.append(abs(closes[idx] - closes[idx - 1]) / prev)
        realized_vol = sum(step_vol) / max(len(step_vol), 1)
        spread_series = []
        for idx in range(len(highs)):
            base = max(abs(opens[idx]), 1e-9)
            spread_series.append((highs[idx] - lows[idx]) / base)
        avg_spread = sum(spread_series) / max(len(spread_series), 1)
        if realized_vol >= 0.02 or avg_spread >= 0.025:
            confidence = min(1.0, max(realized_vol, avg_spread) * 10)
            return RegimeClassification(
                label="volatile",
                confidence=round(confidence, 3),
                explanation=f"realized_vol={realized_vol:.4f}, avg_spread={avg_spread:.4f}",
            )
        if trend_move >= 0.01:
            confidence = min(1.0, abs(trend_move) * 20)
            return RegimeClassification(
                label="trend_up",
                confidence=round(confidence, 3),
                explanation=f"trend_move={trend_move:.4f}, realized_vol={realized_vol:.4f}",
            )
        if trend_move <= -0.01:
            confidence = min(1.0, abs(trend_move) * 20)
            return RegimeClassification(
                label="trend_down",
                confidence=round(confidence, 3),
                explanation=f"trend_move={trend_move:.4f}, realized_vol={realized_vol:.4f}",
            )
        confidence = max(0.2, 1.0 - min(1.0, realized_vol * 10))
        return RegimeClassification(
            label="range",
            confidence=round(confidence, 3),
            explanation=f"trend_move={trend_move:.4f}, realized_vol={realized_vol:.4f}",
        )
