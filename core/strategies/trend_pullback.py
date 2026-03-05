from collections import deque
from typing import Deque

from core.data.models import Candle
from core.strategies.signal import StrategyDecision


class TrendPullbackStrategy:
    def __init__(self) -> None:
        self._closes: Deque[float] = deque(maxlen=3)

    def on_candle(self, candle: Candle) -> StrategyDecision:
        self._closes.append(candle.close)
        if len(self._closes) < 3:
            return StrategyDecision(
                strategy="trend_pullback",
                action="skip",
                direction=None,
                explain="Not enough candles: need 3 closes",
            )
        a, b, c = self._closes
        if c > b > a:
            return StrategyDecision(
                strategy="trend_pullback",
                action="entry",
                direction="BUY",
                explain="Three rising closes (trend resume)",
            )
        if c < b < a:
            return StrategyDecision(
                strategy="trend_pullback",
                action="entry",
                direction="SELL",
                explain="Three falling closes (trend resume)",
            )
        return StrategyDecision(
            strategy="trend_pullback",
            action="skip",
            direction=None,
            explain="No monotonic close sequence",
        )
