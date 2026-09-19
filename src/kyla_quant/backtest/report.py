"""Cost-aware performance metrics and R13 status."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean
from typing import Mapping, Sequence


@dataclass(frozen=True)
class PerformanceReport:
    cagr: float | None
    max_drawdown: float | None
    sharpe: float | None
    win_rate: float | None
    profit_factor: float | None
    expectancy_r: float | None
    sequence_breakdown: Mapping[str, Mapping[str, float]]
    in_sample: Mapping[str, float]
    out_of_sample: Mapping[str, float]
    status: str
    notes: tuple[str, ...] = ()


def _max_drawdown(equity: Sequence[float]) -> float | None:
    if not equity:
        return None
    peak = equity[0]
    drawdown = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak:
            drawdown = max(drawdown, (peak - value) / peak)
    return drawdown


def build_report(*, returns: Sequence[float], r_outcomes: Sequence[float],
                 sequence_breakdown: Mapping[str, Mapping[str, float]],
                 in_sample: Mapping[str, float], out_of_sample: Mapping[str, float],
                 years: float = 1.0, costs_included: bool = False,
                 minimum_cycles: int = 200, kill_switch_tested: bool = False,
                 no_trade_condition_documented: bool = False,
                 mel_approval: bool = False, drawdown_limit: float = 0.2) -> PerformanceReport:
    equity, value = [], 1.0
    for ret in returns:
        value *= 1 + ret
        equity.append(value)
    wins = [r for r in r_outcomes if r > 0]
    losses = [r for r in r_outcomes if r < 0]
    expectancy = mean(r_outcomes) if r_outcomes else None
    gross_win, gross_loss = sum(wins), abs(sum(losses))
    pf = gross_win / gross_loss if gross_loss else (float("inf") if gross_win else None)
    sharpe = (mean(returns) / (sqrt(sum((r - mean(returns)) ** 2 for r in returns) / max(1, len(returns) - 1))) * sqrt(252)) if len(returns) > 1 and sum((r - mean(returns)) ** 2 for r in returns) else None
    dd = _max_drawdown(equity)
    cagr = (value ** (1 / years) - 1) if years > 0 and equity else None
    checks = [costs_included, len(r_outcomes) >= minimum_cycles, (out_of_sample.get("expectancy_r", 0) > 0), (dd is not None and dd <= drawdown_limit), kill_switch_tested, no_trade_condition_documented, mel_approval]
    status = "PASS" if all(checks) else "FAIL" if any(checks) else "INCONCLUSIVE"
    notes = tuple(f"gate_{idx + 1}={'PASS' if check else 'FAIL'}" for idx, check in enumerate(checks))
    return PerformanceReport(cagr, dd, sharpe, len(wins) / len(r_outcomes) if r_outcomes else None, pf, expectancy, sequence_breakdown, in_sample, out_of_sample, status, notes)
