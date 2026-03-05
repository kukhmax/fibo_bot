from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional

from core.data.models import Candle


@dataclass
class StrategySignal:
    direction: str  # "BUY" | "SELL"
    reason: str


class TrendPullbackStrategy:
    def __init__(self) -> None:
        self._closes: Deque[float] = deque(maxlen=3)

    def on_candle(self, candle: Candle) -> Optional[StrategySignal]:
        self._closes.append(candle.close)
        if len(self._closes) < 3:
            return None
        a, b, c = self._closes  # oldest → newest
        if c > b > a:
            return StrategySignal(direction="BUY", reason="Three rising closes (trend resume)")
        if c < b < a:
            return StrategySignal(direction="SELL", reason="Three falling closes (trend resume)")
        return None
