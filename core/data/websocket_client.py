import json
import time

from core.data.models import Tick
from core.data.rest_client import MultiExchangeHistoricalData


class HyperliquidWebSocketParser:
    def parse_tick(self, payload: str, symbol: str) -> Tick | None:
        parsed = json.loads(payload)
        if not isinstance(parsed, dict):
            return None
        data = parsed.get("data") if isinstance(parsed.get("data"), dict) else parsed
        price = _pick(data, "p", "price")
        volume = _pick(data, "v", "size", "volume")
        timestamp = _pick(data, "t", "time", "timestamp")
        if price is None or timestamp is None:
            return None
        return Tick(
            symbol=symbol,
            timestamp_ms=int(timestamp),
            price=float(price),
            volume=float(volume or 0.0),
        )


class LiveDataOrchestrator:
    def __init__(
        self,
        symbol: str,
        timeframe: str,
        rest_data: MultiExchangeHistoricalData | None = None,
        stale_timeout_sec: int = 20,
    ) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.rest_data = rest_data or MultiExchangeHistoricalData()
        self.stale_timeout_sec = stale_timeout_sec
        self.last_ws_timestamp_ms: int | None = None

    def register_ws_tick(self, tick: Tick) -> None:
        if tick.symbol != self.symbol:
            raise ValueError(f"Unexpected symbol: {tick.symbol}")
        self.last_ws_timestamp_ms = tick.timestamp_ms

    def should_use_rest_fallback(self, now_ms: int | None = None) -> bool:
        if self.last_ws_timestamp_ms is None:
            return True
        current_ms = now_ms if now_ms is not None else int(time.time() * 1000)
        return current_ms - self.last_ws_timestamp_ms > self.stale_timeout_sec * 1000

    def fetch_recent_candles(self, limit: int = 200, now_ms: int | None = None):
        if self.should_use_rest_fallback(now_ms=now_ms):
            return self.rest_data.fetch_with_fallback(self.symbol, self.timeframe, limit=limit)
        return []


def _pick(payload: dict, *keys: str):
    for key in keys:
        if key in payload:
            return payload[key]
    return None
