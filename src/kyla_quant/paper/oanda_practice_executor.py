"""OANDA v20 practice executor stub.

This class never sends an order. Implement only after credentials, instrument
mapping, reconciliation, and a paper-test plan are approved.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PracticeOrder:
    instrument: str
    units: float
    side: str
    stop_loss: float
    take_profit: float


class OandaPracticeExecutor:
    def submit(self, order: PracticeOrder, **_: Any) -> dict[str, Any]:
        return {"submitted": False, "reason": "TODO: OANDA practice integration is disabled", "order": order}

    def close(self, trade_id: str) -> dict[str, Any]:
        return {"closed": False, "reason": "TODO: implement reconciled practice close", "trade_id": trade_id}
