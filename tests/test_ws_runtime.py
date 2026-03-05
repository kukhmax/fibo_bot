import asyncio
import json
import unittest

from core.data import HyperliquidWsClient
from core.data import ReconnectPolicy


class _FakeConnection:
    def __init__(self, incoming_messages: list[str], fail_on_recv: bool = False, recv_delay_sec: float = 0.0) -> None:
        self.incoming_messages = list(incoming_messages)
        self.fail_on_recv = fail_on_recv
        self.recv_delay_sec = recv_delay_sec
        self.sent_messages: list[dict] = []
        self.closed = False

    async def send(self, payload: str) -> None:
        self.sent_messages.append(json.loads(payload))

    async def recv(self) -> str:
        if self.recv_delay_sec > 0:
            await asyncio.sleep(self.recv_delay_sec)
        if self.fail_on_recv:
            raise ConnectionError("simulated disconnect")
        if not self.incoming_messages:
            raise ConnectionError("end of stream")
        return self.incoming_messages.pop(0)

    async def close(self) -> None:
        self.closed = True


class TestWsRuntime(unittest.IsolatedAsyncioTestCase):
    async def test_subscribe_and_emit_tick(self) -> None:
        received_ticks = []
        ws = _FakeConnection(['{"data":{"t":1000,"p":"101.5","v":"0.4"}}'])

        async def connector(_: str):
            return ws

        async def on_tick(tick):
            received_ticks.append(tick)

        client = HyperliquidWsClient(
            symbol="BTC",
            timeframe="1m",
            on_tick=on_tick,
            connector=connector,
            reconnect_policy=ReconnectPolicy(initial_delay_sec=0, max_delay_sec=0, jitter_sec=0, max_attempts=1),
        )
        processed = await client.run(max_messages=1)

        self.assertEqual(processed, 1)
        self.assertEqual(len(received_ticks), 1)
        self.assertEqual(received_ticks[0].price, 101.5)
        self.assertEqual(ws.sent_messages[0]["subscription"]["type"], "trades")
        self.assertEqual(ws.sent_messages[1]["subscription"]["type"], "candle")
        self.assertTrue(ws.closed)

    async def test_reconnect_with_backoff(self) -> None:
        received_ticks = []
        first = _FakeConnection([], fail_on_recv=True)
        second = _FakeConnection(['{"data":{"t":2000,"p":"102.0","v":"1.0"}}'])
        sequence = [first, second]
        delays: list[float] = []

        async def connector(_: str):
            return sequence.pop(0)

        async def fake_sleep(delay: float) -> None:
            delays.append(delay)

        client = HyperliquidWsClient(
            symbol="BTC",
            timeframe="1m",
            on_tick=lambda tick: received_ticks.append(tick),
            connector=connector,
            reconnect_policy=ReconnectPolicy(
                initial_delay_sec=0.2,
                max_delay_sec=0.2,
                factor=2.0,
                jitter_sec=0.0,
                max_attempts=3,
            ),
            sleeper=fake_sleep,
        )
        processed = await client.run(max_messages=1)

        self.assertEqual(processed, 1)
        self.assertEqual(len(received_ticks), 1)
        self.assertEqual(delays, [0.2])

    async def test_heartbeat_timeout_causes_retry(self) -> None:
        received_ticks = []
        slow = _FakeConnection([], recv_delay_sec=0.05)
        fast = _FakeConnection(['{"data":{"t":3000,"p":"103.0","v":"0.1"}}'])
        sequence = [slow, fast]
        delays: list[float] = []

        async def connector(_: str):
            return sequence.pop(0)

        async def fake_sleep(delay: float) -> None:
            delays.append(delay)

        client = HyperliquidWsClient(
            symbol="BTC",
            timeframe="1m",
            on_tick=lambda tick: received_ticks.append(tick),
            connector=connector,
            reconnect_policy=ReconnectPolicy(
                initial_delay_sec=0.1,
                max_delay_sec=0.1,
                factor=2.0,
                jitter_sec=0.0,
                max_attempts=3,
            ),
            heartbeat_timeout_sec=0.01,
            sleeper=fake_sleep,
        )
        processed = await client.run(max_messages=1)

        self.assertEqual(processed, 1)
        self.assertEqual(len(received_ticks), 1)
        self.assertEqual(delays, [0.1])


if __name__ == "__main__":
    unittest.main()
