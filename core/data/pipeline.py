import inspect
from typing import Awaitable
from typing import Callable

from core.data.candle_builder import CandleBuilder
from core.data.models import Candle
from core.data.models import Tick
from core.data.websocket_client import HyperliquidWsClient
from core.data.websocket_client import MexcWsClient
from core.data.websocket_client import PrimaryBackupWsClient
from core.data.websocket_client import WsRuntimeProtocol


class RealtimeCandlePipeline:
    def __init__(
        self,
        symbol: str,
        timeframe: str = "5m",
        on_candle: Callable[[Candle], None | Awaitable[None]] | None = None,
        on_tick: Callable[[Tick], None | Awaitable[None]] | None = None,
        ws_client: WsRuntimeProtocol | None = None,
        backup_ws_client: WsRuntimeProtocol | None = None,
    ) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.on_candle = on_candle
        self.on_tick = on_tick
        self._builder = CandleBuilder(symbol=symbol, timeframe=timeframe)
        self._last_emitted_open_time_ms: int | None = None
        if ws_client is not None:
            self._ws_client = ws_client
        else:
            primary = HyperliquidWsClient(
                symbol=symbol,
                timeframe=timeframe,
                on_tick=self.process_tick,
                on_backfill=self.process_backfill,
            )
            backup = backup_ws_client or MexcWsClient(
                symbol=symbol,
                timeframe=timeframe,
                on_tick=self.process_tick,
                on_backfill=self.process_backfill,
            )
            self._ws_client = PrimaryBackupWsClient(primary=primary, backup=backup)

    async def run(self, max_messages: int | None = None) -> int:
        return await self._ws_client.run(max_messages=max_messages)

    async def process_tick(self, tick: Tick) -> None:
        if self.on_tick is not None:
            result = self.on_tick(tick)
            if inspect.isawaitable(result):
                await result
        closed = self._builder.add_tick(tick)
        for candle in closed:
            await self._emit_candle(candle)

    async def process_backfill(self, candles: list[Candle]) -> None:
        ordered = sorted(candles, key=lambda item: item.open_time_ms)
        for candle in ordered:
            if candle.symbol != self.symbol or candle.timeframe != self.timeframe:
                continue
            await self._emit_candle(candle)

    async def flush(self) -> Candle | None:
        current = self._builder.flush()
        if current is not None:
            await self._emit_candle(current)
        return current

    async def _emit_candle(self, candle: Candle) -> None:
        if self._last_emitted_open_time_ms is not None and candle.open_time_ms <= self._last_emitted_open_time_ms:
            return
        self._last_emitted_open_time_ms = candle.open_time_ms
        if self.on_candle is None:
            return
        result = self.on_candle(candle)
        if inspect.isawaitable(result):
            await result
