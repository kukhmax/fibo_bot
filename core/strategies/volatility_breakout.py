from dataclasses import dataclass
from typing import Optional

from core.data.models import Candle


@dataclass
class StrategySignal:
    direction: str  # "BUY" | "SELL"
    reason: str


class VolatilityBreakoutStrategy:
    def __init__(self, lookback: int = 1) -> None:
        self._prev_high: float | None = None
        self._prev_low: float | None = None
        self._initialized = False

    def on_candle(self, candle: Candle) -> Optional[StrategySignal]:
        if not self._initialized:
            self._prev_high = candle.high
            self._prev_low = candle.low
            self._initialized = True
            return None
        signal: StrategySignal | None = None
        if self._prev_high is not None and candle.close > self._prev_high and candle.close > candle.open:
            signal = StrategySignal(direction="BUY", reason="Close breaks previous high")
        elif self._prev_low is not None and candle.close < self._prev_low and candle.close < candle.open:
            signal = StrategySignal(direction="SELL", reason="Close breaks previous low")
        self._prev_high = max(self._prev_high or candle.high, candle.high)
        self._prev_low = min(self._prev_low or candle.low, candle.low)
        return signal
