import json
import unittest

from core.data import MexcWebSocketParser
from core.data import MexcWsClient
from core.data import PrimaryBackupWsClient
from core.data import ReconnectPolicy


class _FakeConnection:
    def __init__(self, incoming_messages: list[str]) -> None:
        self.incoming_messages = list(incoming_messages)
        self.sent_messages: list[dict] = []
        self.closed = False

    async def send(self, payload: str) -> None:
        self.sent_messages.append(json.loads(payload))

    async def recv(self) -> str:
        if not self.incoming_messages:
            raise ConnectionError("end of stream")
        return self.incoming_messages.pop(0)

    async def close(self) -> None:
        self.closed = True


class _FakeWsClient:
    def __init__(self, processed: int) -> None:
        self.processed = processed
        self.called_with: list[int | None] = []
        self.stop_requested = False

    async def run(self, max_messages: int | None = None) -> int:
        self.called_with.append(max_messages)
        return self.processed if max_messages is None else min(self.processed, max_messages)

    def request_stop(self) -> None:
        self.stop_requested = True


class TestMexcWsAdapter(unittest.IsolatedAsyncioTestCase):
    async def test_mexc_parser_parses_tick(self) -> None:
        parser = MexcWebSocketParser()
        tick = parser.parse_tick('{"data":{"t":1000,"p":"201.5","v":"0.7"}}', symbol="BTC_USDT")
        self.assertIsNotNone(tick)
        self.assertEqual(tick.price, 201.5)
        self.assertEqual(tick.volume, 0.7)

    async def test_mexc_ws_client_sends_subscriptions(self) -> None:
        received = []
        ws = _FakeConnection(['{"data":{"t":1000,"p":"201.5","v":"0.7"}}'])

        async def connector(_: str):
            return ws

        client = MexcWsClient(
            symbol="BTC_USDT",
            timeframe="5m",
            on_tick=lambda tick: received.append(tick),
            connector=connector,
            reconnect_policy=ReconnectPolicy(initial_delay_sec=0, max_delay_sec=0, jitter_sec=0, max_attempts=1),
        )
        processed = await client.run(max_messages=1)

        self.assertEqual(processed, 1)
        self.assertEqual(len(received), 1)
        self.assertEqual(ws.sent_messages[0]["method"], "sub.deal")
        self.assertEqual(ws.sent_messages[1]["method"], "sub.kline")
        self.assertTrue(ws.closed)

    async def test_primary_backup_switches_to_backup(self) -> None:
        primary = _FakeWsClient(processed=0)
        backup = _FakeWsClient(processed=2)
        client = PrimaryBackupWsClient(primary=primary, backup=backup)

        processed = await client.run(max_messages=2)

        self.assertEqual(processed, 2)
        self.assertEqual(primary.called_with, [2])
        self.assertEqual(backup.called_with, [2])


if __name__ == "__main__":
    unittest.main()
