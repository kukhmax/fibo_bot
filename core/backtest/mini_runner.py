from dataclasses import dataclass

from core.data.models import Candle
from core.regime import RuleBasedRegimeClassifier
from core.strategies import LiquiditySweepReversalStrategy
from core.strategies import TrendPullbackStrategy
from core.strategies import VolatilityBreakoutStrategy
from core.strategies import select_strategy_by_regime


@dataclass(frozen=True)
class MiniBacktestRunReport:
    candles_count: int
    entries_total: int
    entries_after_ml: int
    entries_blocked_ml: int
    regime_counts: dict[str, int]
    strategy_entry_counts: dict[str, int]


def run_mini_backtest(candles: list[Candle], ml_filter=None) -> MiniBacktestRunReport:
    ordered = sorted(candles, key=lambda item: item.open_time_ms)
    classifier = RuleBasedRegimeClassifier()
    strategies = {
        "trend_pullback": TrendPullbackStrategy(),
        "volatility_breakout": VolatilityBreakoutStrategy(),
        "liquidity_sweep": LiquiditySweepReversalStrategy(),
    }
    entries_total = 0
    entries_after_ml = 0
    entries_blocked_ml = 0
    regime_counts: dict[str, int] = {}
    strategy_entry_counts: dict[str, int] = {}
    window: list[Candle] = []
    for candle in ordered:
        window.append(candle)
        recent = window[-30:]
        regime = classifier.classify(recent)
        regime_counts[regime.label] = regime_counts.get(regime.label, 0) + 1
        strategy_key = select_strategy_by_regime(regime.label)
        strategy = strategies[strategy_key]
        decision = strategy.on_candle(candle)
        if decision.action != "entry":
            continue
        entries_total += 1
        strategy_entry_counts[strategy_key] = strategy_entry_counts.get(strategy_key, 0) + 1
        allow = True
        if ml_filter is not None and bool(getattr(ml_filter, "is_active", lambda: False)()):
            inference = ml_filter.evaluate(recent)
            allow = bool(inference.allow)
        if allow:
            entries_after_ml += 1
        else:
            entries_blocked_ml += 1
    return MiniBacktestRunReport(
        candles_count=len(ordered),
        entries_total=entries_total,
        entries_after_ml=entries_after_ml,
        entries_blocked_ml=entries_blocked_ml,
        regime_counts=regime_counts,
        strategy_entry_counts=strategy_entry_counts,
    )
