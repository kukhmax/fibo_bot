from dataclasses import dataclass
import os

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
    trades: int
    winrate: float
    profit_factor: float
    max_drawdown_r: float
    avg_rr: float
    expectancy_r: float
    is_allowed: bool
    decision_reason: str
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
    trade_r_values: list[float] = []
    window: list[Candle] = []
    for index, candle in enumerate(ordered):
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
            if index + 1 < len(ordered):
                next_candle = ordered[index + 1]
                trade_r_values.append(_estimate_trade_r(candle, next_candle, decision.direction))
        else:
            entries_blocked_ml += 1
    metrics = _calc_metrics(trade_r_values)
    market_quality = _calc_market_quality(ordered)
    allowed, decision_reason = _assess_asset(
        metrics,
        market_quality,
        min_avg_volume=float(os.getenv("WL_MIN_AVG_VOLUME", "50")),
        max_avg_spread_pct=float(os.getenv("WL_MAX_AVG_SPREAD_PCT", "5.0")),
    )
    return MiniBacktestRunReport(
        candles_count=len(ordered),
        entries_total=entries_total,
        entries_after_ml=entries_after_ml,
        entries_blocked_ml=entries_blocked_ml,
        trades=metrics["trades"],
        winrate=metrics["winrate"],
        profit_factor=metrics["profit_factor"],
        max_drawdown_r=metrics["max_drawdown_r"],
        avg_rr=metrics["avg_rr"],
        expectancy_r=metrics["expectancy_r"],
        is_allowed=allowed,
        decision_reason=decision_reason,
        regime_counts=regime_counts,
        strategy_entry_counts=strategy_entry_counts,
    )


def _estimate_trade_r(entry_candle: Candle, next_candle: Candle, direction: str | None) -> float:
    risk_unit = max(entry_candle.high - entry_candle.low, abs(entry_candle.close) * 0.001, 1e-9)
    raw_move = next_candle.close - entry_candle.close
    if direction == "SELL":
        raw_move = -raw_move
    r = raw_move / risk_unit
    if r > 3.0:
        return 3.0
    if r < -3.0:
        return -3.0
    return float(r)


def _calc_metrics(trade_r_values: list[float]) -> dict[str, float | int]:
    trades = len(trade_r_values)
    if trades == 0:
        return {
            "trades": 0,
            "winrate": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_r": 0.0,
            "avg_rr": 0.0,
            "expectancy_r": 0.0,
        }
    wins = [item for item in trade_r_values if item > 0]
    losses = [item for item in trade_r_values if item < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    winrate = len(wins) / trades
    if gross_loss == 0.0:
        profit_factor = gross_profit if gross_profit > 0 else 0.0
    else:
        profit_factor = gross_profit / gross_loss
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    if avg_loss == 0.0:
        avg_rr = avg_win if avg_win > 0 else 0.0
    else:
        avg_rr = avg_win / avg_loss
    expectancy_r = sum(trade_r_values) / trades
    equity = 0.0
    peak = 0.0
    max_drawdown_r = 0.0
    for value in trade_r_values:
        equity += value
        if equity > peak:
            peak = equity
        drawdown = peak - equity
        if drawdown > max_drawdown_r:
            max_drawdown_r = drawdown
    return {
        "trades": trades,
        "winrate": float(winrate),
        "profit_factor": float(profit_factor),
        "max_drawdown_r": float(max_drawdown_r),
        "avg_rr": float(avg_rr),
        "expectancy_r": float(expectancy_r),
    }


def _calc_market_quality(candles: list[Candle]) -> dict[str, float]:
    if not candles:
        return {"avg_volume": 0.0, "avg_spread_pct": 0.0}
    avg_volume = sum(float(item.volume) for item in candles) / len(candles)
    spreads = [((float(item.high) - float(item.low)) / max(abs(float(item.close)), 1e-9)) * 100.0 for item in candles]
    avg_spread_pct = sum(spreads) / len(spreads)
    return {"avg_volume": float(avg_volume), "avg_spread_pct": float(avg_spread_pct)}


def _assess_asset(
    metrics: dict[str, float | int],
    market_quality: dict[str, float],
    min_avg_volume: float,
    max_avg_spread_pct: float,
) -> tuple[bool, str]:
    trades = int(metrics["trades"])
    profit_factor = float(metrics["profit_factor"])
    max_drawdown_r = float(metrics["max_drawdown_r"])
    expectancy_r = float(metrics["expectancy_r"])
    reasons: list[str] = []
    if trades < 20:
        reasons.append("trades<20")
    if profit_factor < 1.2:
        reasons.append("pf<1.2")
    if expectancy_r <= 0.0:
        reasons.append("expectancy<=0")
    if max_drawdown_r > 5.0:
        reasons.append("dd>5R")
    if float(market_quality.get("avg_volume", 0.0)) < float(min_avg_volume):
        reasons.append("liquidity_low")
    if float(market_quality.get("avg_spread_pct", 0.0)) > float(max_avg_spread_pct):
        reasons.append("spread_high")
    if reasons:
        return False, ",".join(reasons)
    return True, "metrics_ok"
