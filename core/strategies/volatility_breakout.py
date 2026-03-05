from core.data.models import Candle
from core.strategies.signal import StrategyDecision


class VolatilityBreakoutStrategy:
    def __init__(self, lookback: int = 1) -> None:
        self._prev_high: float | None = None
        self._prev_low: float | None = None
        self._initialized = False

    def on_candle(self, candle: Candle) -> StrategyDecision:
        if not self._initialized:
            self._prev_high = candle.high
            self._prev_low = candle.low
            self._initialized = True
            return StrategyDecision(
                strategy="volatility_breakout",
                action="skip",
                direction=None,
                explain="Warmup candle stored",
            )
        if self._prev_high is not None and candle.close > self._prev_high and candle.close > candle.open:
            decision = StrategyDecision(
                strategy="volatility_breakout",
                action="entry",
                direction="BUY",
                explain="Close breaks previous high",
            )
        elif self._prev_low is not None and candle.close < self._prev_low and candle.close < candle.open:
            decision = StrategyDecision(
                strategy="volatility_breakout",
                action="entry",
                direction="SELL",
                explain="Close breaks previous low",
            )
        else:
            decision = StrategyDecision(
                strategy="volatility_breakout",
                action="skip",
                direction=None,
                explain="No breakout confirmation",
            )
        self._prev_high = max(self._prev_high or candle.high, candle.high)
        self._prev_low = min(self._prev_low or candle.low, candle.low)
        return decision
