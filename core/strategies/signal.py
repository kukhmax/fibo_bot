from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyDecision:
    strategy: str
    action: str
    direction: str | None
    explain: str
