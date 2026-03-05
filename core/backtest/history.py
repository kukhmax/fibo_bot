from pathlib import Path

from core.data.models import Candle
from core.data.persistence import LocalCandleHistory


def load_local_backtest_candles(
    symbol: str,
    timeframe: str,
    limit: int | None = None,
    history_dir: str | Path = "runtime/history",
) -> list[Candle]:
    storage = LocalCandleHistory(base_dir=history_dir)
    return storage.load(symbol=symbol, timeframe=timeframe, limit=limit)
