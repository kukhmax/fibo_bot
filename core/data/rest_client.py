import json
from urllib import request

from core.data.models import Candle


class HyperliquidRestClient:
    def __init__(self, base_url: str = "https://api.hyperliquid.xyz") -> None:
        self.base_url = base_url.rstrip("/")

    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": symbol,
                "interval": timeframe,
                "startTime": 0,
                "endTime": 0,
                "limit": limit,
            },
        }
        req = request.Request(
            f"{self.base_url}/info",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        raw = _fetch_json(req)
        return _normalize_candles(raw, symbol, timeframe)


class MexcRestClient:
    def __init__(self, base_url: str = "https://contract.mexc.com") -> None:
        self.base_url = base_url.rstrip("/")

    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        query = (
            f"{self.base_url}/api/v1/contract/kline/{symbol}"
            f"?interval={timeframe}&limit={limit}"
        )
        req = request.Request(query, method="GET")
        raw = _fetch_json(req)
        source = raw["data"] if isinstance(raw, dict) and "data" in raw else raw
        return _normalize_candles(source, symbol, timeframe)


class MultiExchangeHistoricalData:
    def __init__(
        self, primary_client: HyperliquidRestClient | None = None, backup_client: MexcRestClient | None = None
    ) -> None:
        self.primary_client = primary_client or HyperliquidRestClient()
        self.backup_client = backup_client or MexcRestClient()

    def fetch_with_fallback(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        try:
            candles = self.primary_client.fetch_candles(symbol=symbol, timeframe=timeframe, limit=limit)
            if candles:
                return candles
        except Exception:
            pass
        return self.backup_client.fetch_candles(symbol=symbol, timeframe=timeframe, limit=limit)


def _fetch_json(req: request.Request):
    with request.urlopen(req, timeout=10) as response:
        body = response.read().decode("utf-8")
    return json.loads(body)


def _normalize_candles(raw, symbol: str, timeframe: str) -> list[Candle]:
    if raw is None:
        return []
    items = raw if isinstance(raw, list) else [raw]
    candles: list[Candle] = []
    for item in items:
        candle = _item_to_candle(item, symbol, timeframe)
        if candle is not None:
            candles.append(candle)
    candles.sort(key=lambda x: x.open_time_ms)
    return candles


def _item_to_candle(item, symbol: str, timeframe: str) -> Candle | None:
    if not isinstance(item, dict):
        return None

    open_time = _pick(item, "t", "openTime", "time", "timestamp")
    close_time = _pick(item, "T", "closeTime")
    open_price = _pick(item, "o", "open")
    high_price = _pick(item, "h", "high")
    low_price = _pick(item, "l", "low")
    close_price = _pick(item, "c", "close")
    volume = _pick(item, "v", "volume")
    if open_time is None or open_price is None or high_price is None or low_price is None or close_price is None:
        return None
    if close_time is None:
        close_time = int(open_time)

    return Candle(
        symbol=symbol,
        timeframe=timeframe,
        open_time_ms=int(open_time),
        close_time_ms=int(close_time),
        open=float(open_price),
        high=float(high_price),
        low=float(low_price),
        close=float(close_price),
        volume=float(volume or 0.0),
    )


def _pick(payload: dict, *keys: str):
    for key in keys:
        if key in payload:
            return payload[key]
    return None
