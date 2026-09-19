"""Fail-closed stance engine and hard gates."""
from __future__ import annotations

from datetime import datetime, timezone

from .schemas import MarketState, Stance, StanceDecision

HARD_GATES = (
    "30-minute event lock",
    "manual kill switch",
    "stale or incomplete data",
    "daily loss or trade-count limit",
    "missing cost model",
    "missing Mel approval for promotion",
)


def decide_stance(state: MarketState, *, manual_kill: bool = False,
                  daily_limit_hit: bool = False, costs_valid: bool = False,
                  mel_approval: bool = False, promotion: bool = False,
                  as_of: datetime | None = None) -> StanceDecision:
    reasons: list[str] = []
    if manual_kill:
        return StanceDecision(Stance.MANUAL_KILL, ("manual kill switch active",), as_of or datetime.now(timezone.utc), HARD_GATES)
    if not state.data_ok:
        reasons.append("data incomplete or unverified")
    if state.news_lock:
        reasons.append("30-minute event lock")
    if daily_limit_hit:
        reasons.append("daily risk limit hit")
    if not costs_valid:
        reasons.append("cost model missing or invalid")
    if promotion and not mel_approval:
        reasons.append("Mel approval missing for promotion")
    if not state.data_ok:
        stance = Stance.DATA_FAILURE
    elif state.news_lock or daily_limit_hit or (promotion and not mel_approval):
        stance = Stance.BLOCKED
    elif not costs_valid:
        stance = Stance.FLAT_ONLY
    else:
        stance = Stance.TRADE_ALLOWED
    return StanceDecision(stance, tuple(reasons), as_of or datetime.now(timezone.utc), HARD_GATES)
