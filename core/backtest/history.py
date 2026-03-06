from pathlib import Path

from core.data.models import Candle
from core.data.persistence import LocalCandleHistory
from core.data.rest_client import MultiExchangeHistoricalData


def load_local_backtest_candles(
    symbol: str,
    timeframe: str,
    limit: int | None = None,
    history_dir: str | Path = "runtime/history",
) -> list[Candle]:
    storage = LocalCandleHistory(base_dir=history_dir)
    return storage.load(symbol=symbol, timeframe=timeframe, limit=limit)


def load_backtest_candles(
    symbol: str,
    timeframe: str,
    limit: int = 3000,
    history_dir: str | Path = "runtime/history",
    historical_data: MultiExchangeHistoricalData | None = None,
) -> list[Candle]:
    storage = LocalCandleHistory(base_dir=history_dir)
    local = storage.load(symbol=symbol, timeframe=timeframe, limit=limit)
    if len(local) >= limit:
        return local[-limit:]
    remote: list[Candle] = []
    provider = historical_data or MultiExchangeHistoricalData()
    try:
        remote = provider.fetch_with_fallback(symbol=symbol, timeframe=timeframe, limit=limit)
    except Exception:
        remote = []
    local_open_times = {item.open_time_ms for item in local}
    appended_open_times: set[int] = set()
    for candle in remote:
        if candle.open_time_ms in local_open_times or candle.open_time_ms in appended_open_times:
            continue
        storage.append(candle)
        appended_open_times.add(candle.open_time_ms)
    merged = _merge_candles(local=local, remote=remote)
    if limit > 0:
        return merged[-limit:]
    return merged


def _merge_candles(local: list[Candle], remote: list[Candle]) -> list[Candle]:
    by_open_time: dict[int, Candle] = {}
    for candle in remote:
        if candle.symbol == "" or candle.timeframe == "":
            continue
        by_open_time[candle.open_time_ms] = candle
    for candle in local:
        if candle.symbol == "" or candle.timeframe == "":
            continue
        by_open_time[candle.open_time_ms] = candle
    merged = list(by_open_time.values())
    merged.sort(key=lambda item: item.open_time_ms)
    return merged
