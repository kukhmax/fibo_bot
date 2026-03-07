import json
import time
from urllib import request

from core.data.models import Candle


class HyperliquidRestClient:
    def __init__(self, base_url: str = "https://api.hyperliquid.xyz") -> None:
        self.base_url = base_url.rstrip("/")

    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        # Normalize symbol: remove USDT suffix if present (Hyperliquid uses ETH, BTC, SOL)
        coin = symbol.replace("USDT", "") if symbol.endswith("USDT") else symbol
        
        # Calculate time range
        now_ms = int(time.time() * 1000)
        tf_ms = _tf_to_ms(timeframe)
        start_time = now_ms - (limit * tf_ms)
        
        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": coin,
                "interval": timeframe,
                "startTime": start_time,
                "endTime": now_ms,
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
        # Normalize symbol: ensure _USDT suffix (Mexc uses ETH_USDT)
        mexc_symbol = symbol
        if "USDT" in symbol and "_" not in symbol:
             mexc_symbol = symbol.replace("USDT", "_USDT")
            
        # Mexc timeframe mapping
        interval_map = {"1m": "Min1", "5m": "Min5", "15m": "Min15", "30m": "Min30", "1h": "Min60", "4h": "Min240"}
        mexc_interval = interval_map.get(timeframe, "Min60")

        query = (
            f"{self.base_url}/api/v1/contract/kline/{mexc_symbol}"
            f"?interval={mexc_interval}&limit={limit}"
        )
        req = request.Request(query, method="GET")
        raw = _fetch_json(req)
        source = raw["data"] if isinstance(raw, dict) and "data" in raw else raw
        
        # Handle Mexc column-oriented data (dict of lists)
        if isinstance(source, dict) and "time" in source and isinstance(source["time"], list):
            count = len(source["time"])
            converted = []
            for i in range(count):
                converted.append({
                    "time": source["time"][i],
                    "open": source["open"][i],
                    "high": source["high"][i],
                    "low": source["low"][i],
                    "close": source["close"][i],
                    "vol": source["vol"][i],
                })
            source = converted
            
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
        except Exception as e:
            print(f"Primary source failed for {symbol}: {e}")
        
        try:
            return self.backup_client.fetch_candles(symbol=symbol, timeframe=timeframe, limit=limit)
        except Exception as e:
            print(f"Backup source failed for {symbol}: {e}")
            return []


def _tf_to_ms(tf: str) -> int:
    if tf.endswith("m"):
        return int(tf[:-1]) * 60_000
    if tf.endswith("h"):
        return int(tf[:-1]) * 3_600_000
    if tf.endswith("d"):
        return int(tf[:-1]) * 86_400_000
    return 60_000


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
    volume = _pick(item, "v", "volume", "vol")

    if open_time is None or open_price is None or high_price is None or low_price is None or close_price is None:
        return None
    
    open_time = int(open_time)
    # Heuristic: if timestamp is small (seconds), convert to ms
    if open_time < 10_000_000_000:
        open_time *= 1000

    if close_time is None:
        close_time = open_time + _tf_to_ms(timeframe) - 1
    else:
        close_time = int(close_time)
        if close_time < 10_000_000_000:
            close_time *= 1000

    return Candle(
        symbol=symbol,
        timeframe=timeframe,
        open_time_ms=open_time,
        close_time_ms=close_time,
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
