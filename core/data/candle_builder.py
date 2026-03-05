from core.data.models import Candle
from core.data.models import Tick


TIMEFRAME_TO_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "1h": 3_600_000,
}


class CandleBuilder:
    def __init__(self, symbol: str, timeframe: str) -> None:
        if timeframe not in TIMEFRAME_TO_MS:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        self.symbol = symbol
        self.timeframe = timeframe
        self._duration_ms = TIMEFRAME_TO_MS[timeframe]
        self._current_candle: Candle | None = None

    def add_tick(self, tick: Tick) -> list[Candle]:
        if tick.symbol != self.symbol:
            raise ValueError(f"Unexpected symbol: {tick.symbol}")

        bucket_open = self._bucket_open_time(tick.timestamp_ms)
        closed: list[Candle] = []

        if self._current_candle is None:
            self._current_candle = self._new_candle(bucket_open, tick)
            return closed

        if bucket_open == self._current_candle.open_time_ms:
            self._current_candle = Candle(
                symbol=self.symbol,
                timeframe=self.timeframe,
                open_time_ms=self._current_candle.open_time_ms,
                close_time_ms=self._current_candle.close_time_ms,
                open=self._current_candle.open,
                high=max(self._current_candle.high, tick.price),
                low=min(self._current_candle.low, tick.price),
                close=tick.price,
                volume=self._current_candle.volume + tick.volume,
            )
            return closed

        closed.append(self._current_candle)
        self._current_candle = self._new_candle(bucket_open, tick)
        return closed

    def flush(self) -> Candle | None:
        candle = self._current_candle
        self._current_candle = None
        return candle

    def _bucket_open_time(self, timestamp_ms: int) -> int:
        return (timestamp_ms // self._duration_ms) * self._duration_ms

    def _new_candle(self, bucket_open: int, tick: Tick) -> Candle:
        return Candle(
            symbol=self.symbol,
            timeframe=self.timeframe,
            open_time_ms=bucket_open,
            close_time_ms=bucket_open + self._duration_ms - 1,
            open=tick.price,
            high=tick.price,
            low=tick.price,
            close=tick.price,
            volume=tick.volume,
        )
