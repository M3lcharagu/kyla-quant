"""Probe-cycle mechanics."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProbeTrade:
    number: int
    risk_r: float
    outcome_r: float | None = None


@dataclass(frozen=True)
class ProbeCycle:
    trades: tuple[ProbeTrade, ...]
    max_trades: int = 3

    @property
    def expected_pre_cost_math(self) -> str:
        return "2x+1R - 0.25R = +1.75R per cycle before costs"

    @property
    def total_outcome_r(self) -> float | None:
        if any(trade.outcome_r is None for trade in self.trades):
            return None
        return sum(trade.outcome_r or 0.0 for trade in self.trades)


def create_probe_cycle(*, first_two_risk: float = 1.0, probe_risk: float = 0.25) -> ProbeCycle:
    """Create the 2:1 sequence: two full-size trades and one minimal probe."""
    if first_two_risk <= 0 or probe_risk <= 0:
        raise ValueError("risk values must be positive")
    return ProbeCycle((ProbeTrade(1, first_two_risk), ProbeTrade(2, first_two_risk), ProbeTrade(3, probe_risk)))
