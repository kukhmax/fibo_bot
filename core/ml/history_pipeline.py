from core.data.models import Candle
from core.data.persistence import LocalCandleHistory
from core.data.rest_client import MultiExchangeHistoricalData


class HistoricalTrainingDataPipeline:
    def __init__(
        self,
        symbol: str,
        timeframe: str,
        min_candles: int = 500,
        local_history: LocalCandleHistory | None = None,
        historical_data: MultiExchangeHistoricalData | None = None,
    ) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.min_candles = min_candles
        self.local_history = local_history or LocalCandleHistory()
        self.historical_data = historical_data or MultiExchangeHistoricalData()

    def build(self, limit: int = 1000) -> list[Candle]:
        local = self.local_history.load(self.symbol, self.timeframe, limit=limit)
        missing = max(0, self.min_candles - len(local))
        remote: list[Candle] = []
        if missing > 0:
            remote_limit = max(missing, min(limit, self.min_candles))
            remote = self.historical_data.fetch_with_fallback(
                symbol=self.symbol,
                timeframe=self.timeframe,
                limit=remote_limit,
            )
        merged = _merge_candles(remote=remote, local=local)
        if limit > 0:
            return merged[-limit:]
        return merged


def _merge_candles(remote: list[Candle], local: list[Candle]) -> list[Candle]:
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
