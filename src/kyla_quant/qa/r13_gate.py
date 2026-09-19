"""R13 rejection checks."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GateEvidence:
    costs_included: bool
    no_leakage: bool
    cycles: int
    positive_oos_expectancy: bool
    drawdown_fits: bool
    kill_switch_tested: bool
    no_trade_condition_documented: bool
    mel_approval: bool


@dataclass(frozen=True)
class GateResult:
    status: str
    failed_checks: tuple[str, ...]
    required_approval: str = "Mel approval required for research→paper and paper→live"


def evaluate_r13(evidence: GateEvidence, *, minimum_cycles: int = 200) -> GateResult:
    checks = {
        "costs_included": evidence.costs_included,
        "no_leakage": evidence.no_leakage,
        "200+ cycles": evidence.cycles >= minimum_cycles,
        "positive OOS expectancy": evidence.positive_oos_expectancy,
        "drawdown fits": evidence.drawdown_fits,
        "kill switch tested": evidence.kill_switch_tested,
        "no-trade condition documented": evidence.no_trade_condition_documented,
        "Mel approval": evidence.mel_approval,
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    if failed:
        return GateResult("FAIL" if any(checks.values()) else "INCONCLUSIVE", failed)
    return GateResult("PASS", ())
