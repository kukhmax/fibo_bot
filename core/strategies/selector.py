def select_strategy_by_regime(regime_label: str, fallback: str = "trend_pullback") -> str:
    label = regime_label.strip().lower()
    if label == "volatile":
        return "volatility_breakout"
    if label in {"trend_up", "trend_down"}:
        return "trend_pullback"
    if label == "range":
        return "liquidity_sweep"
    return fallback
