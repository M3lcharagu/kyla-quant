"""Hyperliquid shadow-mode stub: observe and log, never submit."""
from __future__ import annotations

from typing import Any


class HyperliquidShadow:
    def observe(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"mode": "shadow", "submitted": False, "payload": payload, "reason": "TODO: connect only to a read-only/shadow interface"}
