import asyncio
from dataclasses import dataclass
import inspect
import json
import logging
import random
import time
from typing import Awaitable
from typing import Callable
from typing import Protocol

from core.data.candle_builder import TIMEFRAME_TO_MS
from core.data.models import Candle
from core.data.models import Tick
from core.data.rest_client import MultiExchangeHistoricalData


logger = logging.getLogger(__name__)


class WsConnectionProtocol(Protocol):
    async def send(self, payload: str) -> None:
        ...

    async def recv(self) -> str:
        ...

    async def close(self) -> None:
        ...


WsConnector = Callable[[str], Awaitable[WsConnectionProtocol]]


class WsRuntimeProtocol(Protocol):
    async def run(self, max_messages: int | None = None) -> int:
        ...

    def request_stop(self) -> None:
        ...


@dataclass(frozen=True)
class ReconnectPolicy:
    initial_delay_sec: float = 1.0
    max_delay_sec: float = 20.0
    factor: float = 2.0
    jitter_sec: float = 0.3
    max_attempts: int | None = None

    def delay_for_attempt(self, attempt: int) -> float:
        base = min(self.initial_delay_sec * (self.factor ** max(0, attempt - 1)), self.max_delay_sec)
        if self.jitter_sec <= 0:
            return base
        return max(0.0, base + random.uniform(0, self.jitter_sec))


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


class MexcWebSocketParser:
    def parse_tick(self, payload: str, symbol: str) -> Tick | None:
        parsed = json.loads(payload)
        if not isinstance(parsed, dict):
            return None
        data = parsed.get("data")
        if isinstance(data, list) and data:
            data = data[0]
        if not isinstance(data, dict):
            data = parsed
        price = _pick(data, "p", "price")
        volume = _pick(data, "v", "vol", "size", "quantity")
        timestamp = _pick(data, "t", "time", "ts")
        if price is None or timestamp is None:
            return None
        return Tick(
            symbol=symbol,
            timestamp_ms=int(timestamp),
            price=float(price),
            volume=float(volume or 0.0),
        )


class HyperliquidWsClient:
    def __init__(
        self,
        symbol: str,
        timeframe: str = "5m",
        parser: HyperliquidWebSocketParser | None = None,
        on_tick: Callable[[Tick], None | Awaitable[None]] | None = None,
        on_backfill: Callable[[list[Candle]], None | Awaitable[None]] | None = None,
        rest_data: MultiExchangeHistoricalData | None = None,
        ws_url: str = "wss://api.hyperliquid.xyz/ws",
        connector: WsConnector | None = None,
        reconnect_policy: ReconnectPolicy | None = None,
        heartbeat_timeout_sec: float = 20.0,
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock_ms: Callable[[], int] | None = None,
    ) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.parser = parser or HyperliquidWebSocketParser()
        self.on_tick = on_tick
        self.on_backfill = on_backfill
        self.rest_data = rest_data or MultiExchangeHistoricalData()
        self.ws_url = ws_url
        self.connector = connector or default_ws_connector
        self.reconnect_policy = reconnect_policy or ReconnectPolicy()
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.sleeper = sleeper
        self.clock_ms = clock_ms or _now_ms
        self._timeframe_ms = TIMEFRAME_TO_MS.get(self.timeframe, 60_000)
        self._last_tick_timestamp_ms: int | None = None
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    async def run(self, max_messages: int | None = None) -> int:
        total_processed = 0
        reconnect_attempt = 0
        while not self._stop_requested:
            try:
                logger.info(f"ws_connecting url={self.ws_url} attempt={reconnect_attempt}")
                connection = await self.connector(self.ws_url)
                logger.info(f"ws_connected url={self.ws_url}")
                needs_backfill = reconnect_attempt > 0
                reconnect_attempt = 0
                if needs_backfill:
                    await self._restore_gap_with_rest()
                remaining = None if max_messages is None else max(0, max_messages - total_processed)
                processed = await self._consume_connection(connection, remaining_limit=remaining)
                total_processed += processed
                if max_messages is not None and total_processed >= max_messages:
                    return total_processed
                if not self._stop_requested:
                    raise ConnectionError("websocket stream closed")
            except Exception as exc:
                if self._stop_requested:
                    break
                logger.warning(f"ws_error url={self.ws_url} error={exc}")
                reconnect_attempt += 1
                if (
                    self.reconnect_policy.max_attempts is not None
                    and reconnect_attempt > self.reconnect_policy.max_attempts
                ):
                    break
                delay = self.reconnect_policy.delay_for_attempt(reconnect_attempt)
                await self.sleeper(delay)
        return total_processed

    async def _consume_connection(
        self, connection: WsConnectionProtocol, remaining_limit: int | None = None
    ) -> int:
        processed = 0
        try:
            await self._send_subscriptions(connection)
            logger.info(f"ws_subscribed symbol={self.symbol} timeframe={self.timeframe}")
            while not self._stop_requested:
                if remaining_limit is not None and processed >= remaining_limit:
                    return processed
                try:
                    raw_message = await asyncio.wait_for(connection.recv(), timeout=self.heartbeat_timeout_sec)
                except Exception:
                    logger.warning(f"ws_heartbeat_timeout symbol={self.symbol}")
                    return processed
                tick = self.parser.parse_tick(raw_message, symbol=self.symbol)
                if tick is None:
                    continue
                self._last_tick_timestamp_ms = tick.timestamp_ms
                await self._emit_tick(tick)
                processed += 1
        finally:
            logger.info(f"ws_closed symbol={self.symbol} processed={processed}")
            try:
                await connection.close()
            except Exception:
                pass
        return processed

    async def _send_subscriptions(self, connection: WsConnectionProtocol) -> None:
        trade_subscription = {
            "method": "subscribe",
            "subscription": {"type": "trades", "coin": self.symbol},
        }
        candle_subscription = {
            "method": "subscribe",
            "subscription": {"type": "candle", "coin": self.symbol, "interval": self.timeframe},
        }
        await connection.send(json.dumps(trade_subscription))
        await connection.send(json.dumps(candle_subscription))

    async def _emit_tick(self, tick: Tick) -> None:
        if self.on_tick is None:
            return
        result = self.on_tick(tick)
        if inspect.isawaitable(result):
            await result

    async def _emit_backfill(self, candles: list[Candle]) -> None:
        if self.on_backfill is None:
            return
        result = self.on_backfill(candles)
        if inspect.isawaitable(result):
            await result

    async def _restore_gap_with_rest(self) -> None:
        if self._last_tick_timestamp_ms is None:
            return
        limit = self._estimate_backfill_limit()
        if limit <= 0:
            return
        logger.info(f"ws_backfill_start symbol={self.symbol} limit={limit} last_tick={self._last_tick_timestamp_ms}")
        candles = self.rest_data.fetch_with_fallback(symbol=self.symbol, timeframe=self.timeframe, limit=limit)
        filtered = [candle for candle in candles if candle.open_time_ms > self._last_tick_timestamp_ms]
        if not filtered:
            return
        await self._emit_backfill(filtered)
        logger.info(f"ws_backfill_complete symbol={self.symbol} count={len(filtered)}")
        self._last_tick_timestamp_ms = max(self._last_tick_timestamp_ms, filtered[-1].close_time_ms)

    def _estimate_backfill_limit(self) -> int:
        if self._last_tick_timestamp_ms is None:
            return 0
        gap_ms = self.clock_ms() - self._last_tick_timestamp_ms
        if gap_ms <= self._timeframe_ms:
            return 0
        candle_count = (gap_ms // self._timeframe_ms) + 2
        return int(max(1, min(500, candle_count)))


class MexcWsClient(HyperliquidWsClient):
    def __init__(
        self,
        symbol: str,
        timeframe: str = "5m",
        parser: MexcWebSocketParser | None = None,
        on_tick: Callable[[Tick], None | Awaitable[None]] | None = None,
        on_backfill: Callable[[list[Candle]], None | Awaitable[None]] | None = None,
        rest_data: MultiExchangeHistoricalData | None = None,
        ws_url: str = "wss://contract.mexc.com/edge",
        connector: WsConnector | None = None,
        reconnect_policy: ReconnectPolicy | None = None,
        heartbeat_timeout_sec: float = 20.0,
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock_ms: Callable[[], int] | None = None,
    ) -> None:
        super().__init__(
            symbol=symbol,
            timeframe=timeframe,
            parser=parser or MexcWebSocketParser(),
            on_tick=on_tick,
            on_backfill=on_backfill,
            rest_data=rest_data,
            ws_url=ws_url,
            connector=connector,
            reconnect_policy=reconnect_policy,
            heartbeat_timeout_sec=heartbeat_timeout_sec,
            sleeper=sleeper,
            clock_ms=clock_ms,
        )

    async def _send_subscriptions(self, connection: WsConnectionProtocol) -> None:
        trade_subscription = {
            "method": "sub.deal",
            "param": {"symbol": self.symbol},
        }
        candle_subscription = {
            "method": "sub.kline",
            "param": {"symbol": self.symbol, "interval": self.timeframe},
        }
        await connection.send(json.dumps(trade_subscription))
        await connection.send(json.dumps(candle_subscription))


class PrimaryBackupWsClient:
    def __init__(self, primary: WsRuntimeProtocol, backup: WsRuntimeProtocol | None = None) -> None:
        self.primary = primary
        self.backup = backup

    async def run(self, max_messages: int | None = None) -> int:
        processed = await self.primary.run(max_messages=max_messages)
        if self.backup is None:
            return processed
        if max_messages is None and processed > 0:
            return processed
        remaining = None if max_messages is None else max(0, max_messages - processed)
        if remaining == 0:
            return processed
        backup_processed = await self.backup.run(max_messages=remaining)
        return processed + backup_processed

    def request_stop(self) -> None:
        self.primary.request_stop()
        if self.backup is not None:
            self.backup.request_stop()


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


async def default_ws_connector(url: str) -> WsConnectionProtocol:
    try:
        import websockets
    except ImportError as exc:
        raise RuntimeError("websockets library is required for live ws runtime") from exc
    return await websockets.connect(url, ping_interval=None)


def _now_ms() -> int:
    return int(time.time() * 1000)
