import time
from typing import Callable

from core.data.models import Candle
from core.data.models import DataQualityReport
from core.data.models import Tick
from core.data.candle_builder import TIMEFRAME_TO_MS


def validate_candle_sequence(symbol: str, timeframe: str, candles: list[Candle]) -> DataQualityReport:
    if timeframe not in TIMEFRAME_TO_MS:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    if not candles:
        return DataQualityReport(symbol=symbol, timeframe=timeframe, is_valid=False, issues=("no_data",))

    issues: list[str] = []
    expected_step = TIMEFRAME_TO_MS[timeframe]
    previous_open: int | None = None

    for candle in candles:
        if candle.symbol != symbol:
            issues.append("symbol_mismatch")
        if candle.timeframe != timeframe:
            issues.append("timeframe_mismatch")
        if candle.high < candle.low:
            issues.append("invalid_high_low")
        if candle.volume < 0:
            issues.append("negative_volume")
        if previous_open is not None:
            delta = candle.open_time_ms - previous_open
            if delta < expected_step:
                issues.append("overlapping_candles")
            elif delta > expected_step:
                issues.append("gap_detected")
        previous_open = candle.open_time_ms

    unique_issues = tuple(sorted(set(issues)))
    return DataQualityReport(
        symbol=symbol,
        timeframe=timeframe,
        is_valid=len(unique_issues) == 0,
        issues=unique_issues,
    )


class RuntimeDataQualityMonitor:
    def __init__(
        self,
        symbol: str,
        timeframe: str,
        stale_timeout_ms: int = 20_000,
        max_timestamp_drift_ms: int = 5_000,
        clock_ms: Callable[[], int] | None = None,
    ) -> None:
        if timeframe not in TIMEFRAME_TO_MS:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        self.symbol = symbol
        self.timeframe = timeframe
        self.stale_timeout_ms = stale_timeout_ms
        self.max_timestamp_drift_ms = max_timestamp_drift_ms
        self.clock_ms = clock_ms or _now_ms
        self._last_tick_timestamp_ms: int | None = None
        self._last_candle_open_time_ms: int | None = None

    def evaluate_tick(self, tick: Tick) -> DataQualityReport:
        issues: list[str] = []
        if tick.symbol != self.symbol:
            issues.append("symbol_mismatch")
        now_ms = self.clock_ms()
        if tick.timestamp_ms - now_ms > self.max_timestamp_drift_ms:
            issues.append("timestamp_drift")
        self._last_tick_timestamp_ms = tick.timestamp_ms
        return _make_report(self.symbol, self.timeframe, issues)

    def evaluate_candle(self, candle: Candle) -> DataQualityReport:
        issues: list[str] = []
        if candle.symbol != self.symbol:
            issues.append("symbol_mismatch")
        if candle.timeframe != self.timeframe:
            issues.append("timeframe_mismatch")
        if candle.high < candle.low:
            issues.append("invalid_high_low")
        if candle.volume < 0:
            issues.append("negative_volume")
        if self._last_candle_open_time_ms is not None:
            delta = candle.open_time_ms - self._last_candle_open_time_ms
            expected = TIMEFRAME_TO_MS[self.timeframe]
            if delta < expected:
                issues.append("overlapping_candles")
            elif delta > expected:
                issues.append("gap_detected")
        now_ms = self.clock_ms()
        if candle.close_time_ms - now_ms > self.max_timestamp_drift_ms:
            issues.append("timestamp_drift")
        self._last_candle_open_time_ms = candle.open_time_ms
        return _make_report(self.symbol, self.timeframe, issues)

    def evaluate_staleness(self) -> DataQualityReport:
        if self._last_tick_timestamp_ms is None:
            return _make_report(self.symbol, self.timeframe, ["stale_stream"])
        now_ms = self.clock_ms()
        if now_ms - self._last_tick_timestamp_ms > self.stale_timeout_ms:
            return _make_report(self.symbol, self.timeframe, ["stale_stream"])
        return _make_report(self.symbol, self.timeframe, [])


def _make_report(symbol: str, timeframe: str, issues: list[str]) -> DataQualityReport:
    unique_issues = tuple(sorted(set(issues)))
    return DataQualityReport(
        symbol=symbol,
        timeframe=timeframe,
        is_valid=len(unique_issues) == 0,
        issues=unique_issues,
    )


def _now_ms() -> int:
    return int(time.time() * 1000)
