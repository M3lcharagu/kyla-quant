"""Walk-forward runner boundary around backtesting.py.

The wrapper is intentionally data-agnostic: a caller supplies a strategy and
clean, time-ordered data. It refuses to call a result out-of-sample unless the
split is explicit.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class CostModel:
    spread: float
    slippage: float
    commission: float

    def validate(self) -> None:
        if min(self.spread, self.slippage, self.commission) < 0:
            raise ValueError("costs cannot be negative")


@dataclass(frozen=True)
class WalkForwardSplit:
    train: Sequence[Any]
    test: Sequence[Any]
    train_fraction: float


def split_train_test(data: Sequence[Any], train_fraction: float = 0.7) -> WalkForwardSplit:
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    pivot = int(len(data) * train_fraction)
    if pivot == 0 or pivot == len(data):
        raise ValueError("data must contain both train and test observations")
    return WalkForwardSplit(data[:pivot], data[pivot:], train_fraction)


def run_walk_forward(data: Sequence[Any], strategy: Any, *, costs: CostModel,
                     train_fraction: float = 0.7, minimum_cycles: int = 200) -> dict[str, Any]:
    """Run a strategy hook when supplied; return an auditable, unvalidated result."""
    costs.validate()
    split = split_train_test(data, train_fraction)
    if len(data) < minimum_cycles:
        return {"status": "INCONCLUSIVE", "reason": f"minimum {minimum_cycles} cycles not met", "train_size": len(split.train), "test_size": len(split.test), "costs": costs}
    if not hasattr(strategy, "fit") or not hasattr(strategy, "evaluate"):
        return {"status": "INCONCLUSIVE", "reason": "strategy must expose fit and evaluate", "costs": costs}
    strategy.fit(split.train)
    train = strategy.evaluate(split.train, costs=costs)
    out_of_sample = strategy.evaluate(split.test, costs=costs)
    return {"status": "PENDING_REPORT", "train": train, "out_of_sample": out_of_sample, "costs": costs, "minimum_cycles": minimum_cycles}
