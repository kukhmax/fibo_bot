import unittest

from core.data import Candle
from core.data import HyperliquidWebSocketParser
from core.data import LiveDataOrchestrator
from core.data import MultiExchangeHistoricalData


class _PrimaryClientFail:
    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 200):
        raise RuntimeError("primary unavailable")


class _BackupClientOk:
    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 200):
        return [
            Candle(
                symbol=symbol,
                timeframe=timeframe,
                open_time_ms=0,
                close_time_ms=59_999,
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1.0,
            )
        ]


class TestDataFallback(unittest.TestCase):
    def test_rest_fallback_to_backup_exchange(self) -> None:
        source = MultiExchangeHistoricalData(
            primary_client=_PrimaryClientFail(),
            backup_client=_BackupClientOk(),
        )
        candles = source.fetch_with_fallback(symbol="BTC", timeframe="1m", limit=5)
        self.assertEqual(len(candles), 1)
        self.assertEqual(candles[0].symbol, "BTC")

    def test_orchestrator_uses_rest_when_ws_stale(self) -> None:
        source = MultiExchangeHistoricalData(
            primary_client=_PrimaryClientFail(),
            backup_client=_BackupClientOk(),
        )
        orchestrator = LiveDataOrchestrator(
            symbol="BTC",
            timeframe="1m",
            rest_data=source,
            stale_timeout_sec=5,
        )

        candles = orchestrator.fetch_recent_candles(limit=5, now_ms=10_000)
        self.assertEqual(len(candles), 1)

    def test_orchestrator_skips_rest_when_ws_fresh(self) -> None:
        source = MultiExchangeHistoricalData(
            primary_client=_PrimaryClientFail(),
            backup_client=_BackupClientOk(),
        )
        parser = HyperliquidWebSocketParser()
        tick = parser.parse_tick('{"data":{"t":10000,"p":"101.2","v":"0.2"}}', symbol="BTC")
        self.assertIsNotNone(tick)
        orchestrator = LiveDataOrchestrator(
            symbol="BTC",
            timeframe="1m",
            rest_data=source,
            stale_timeout_sec=30,
        )
        orchestrator.register_ws_tick(tick)
        candles = orchestrator.fetch_recent_candles(limit=5, now_ms=20_000)
        self.assertEqual(candles, [])


if __name__ == "__main__":
    unittest.main()
