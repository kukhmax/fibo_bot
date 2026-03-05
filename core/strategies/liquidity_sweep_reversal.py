from dataclasses import dataclass
from typing import Optional

from core.data.models import Candle


@dataclass
class StrategySignal:
    direction: str
    reason: str


class LiquiditySweepReversalStrategy:
    def __init__(self) -> None:
        self._prev: Candle | None = None

    def on_candle(self, candle: Candle) -> Optional[StrategySignal]:
        if self._prev is None:
            self._prev = candle
            return None
        prev = self._prev
        self._prev = candle
        if candle.low < prev.low and candle.close > prev.low and candle.close > candle.open:
            return StrategySignal(direction="BUY", reason="Sweep below prev low, bullish reclaim")
        if candle.high > prev.high and candle.close < prev.high and candle.close < candle.open:
            return StrategySignal(direction="SELL", reason="Sweep above prev high, bearish reclaim")
        return None
