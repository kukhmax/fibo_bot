from core.data.models import Candle
from core.data.models import DataQualityReport
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
