from dataclasses import dataclass


@dataclass(frozen=True)
class RiskCheckResult:
    allowed: bool
    risk_per_trade_pct: float
    reason: str


class RiskManager:
    def __init__(self, min_risk_per_trade_pct: float = 0.1, max_risk_per_trade_pct: float = 2.0) -> None:
        self.min_risk_per_trade_pct = min_risk_per_trade_pct
        self.max_risk_per_trade_pct = max_risk_per_trade_pct

    def validate_risk_per_trade_pct(self, raw_value: float) -> RiskCheckResult:
        value = float(raw_value)
        if value < self.min_risk_per_trade_pct:
            return RiskCheckResult(
                allowed=False,
                risk_per_trade_pct=value,
                reason=f"risk должен быть в диапазоне {self.min_risk_per_trade_pct}..{self.max_risk_per_trade_pct}",
            )
        if value > self.max_risk_per_trade_pct:
            return RiskCheckResult(
                allowed=False,
                risk_per_trade_pct=self.max_risk_per_trade_pct,
                reason=f"risk должен быть в диапазоне {self.min_risk_per_trade_pct}..{self.max_risk_per_trade_pct}",
            )
        return RiskCheckResult(allowed=True, risk_per_trade_pct=value, reason="ok")

    def calc_risk_amount(self, balance: float, risk_per_trade_pct: float) -> float:
        if balance <= 0:
            return 0.0
        checked = self.validate_risk_per_trade_pct(risk_per_trade_pct)
        if not checked.allowed:
            return 0.0
        return balance * (checked.risk_per_trade_pct / 100.0)

    def calc_position_size(self, entry_price: float, stop_price: float, risk_amount: float) -> float:
        distance = abs(entry_price - stop_price)
        if distance <= 0 or risk_amount <= 0:
            return 0.0
        return risk_amount / distance
