from core.data.models import Candle
from core.strategies.signal import StrategyDecision


class LiquiditySweepReversalStrategy:
    def __init__(self) -> None:
        self._prev: Candle | None = None

    def on_candle(self, candle: Candle) -> StrategyDecision:
        if self._prev is None:
            self._prev = candle
            return StrategyDecision(
                strategy="liquidity_sweep",
                action="skip",
                direction=None,
                explain="Warmup candle stored",
            )
        prev = self._prev
        self._prev = candle
        if candle.low < prev.low and candle.close > prev.low and candle.close > candle.open:
            return StrategyDecision(
                strategy="liquidity_sweep",
                action="entry",
                direction="BUY",
                explain="Sweep below prev low, bullish reclaim",
            )
        if candle.high > prev.high and candle.close < prev.high and candle.close < candle.open:
            return StrategyDecision(
                strategy="liquidity_sweep",
                action="entry",
                direction="SELL",
                explain="Sweep above prev high, bearish reclaim",
            )
        return StrategyDecision(
            strategy="liquidity_sweep",
            action="skip",
            direction=None,
            explain="No sweep reclaim pattern",
        )
