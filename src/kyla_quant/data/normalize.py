"""Normalize source records into a venue-tagged, UTC-oriented shape."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


def _utc(value: datetime | str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def normalize_record(record: Mapping[str, Any], *, venue: str, symbol: str) -> dict[str, Any]:
    """Return a stable record; preserve bid/ask when available and never invent quotes."""
    timestamp = record.get("timestamp", record.get("time", record.get("datetime")))
    normalized: dict[str, Any] = {
        "timestamp": _utc(timestamp),
        "venue": venue,
        "symbol": symbol,
        "open": record.get("open"),
        "high": record.get("high"),
        "low": record.get("low"),
        "close": record.get("close"),
        "volume": record.get("volume"),
        "bid": record.get("bid"),
        "ask": record.get("ask"),
        "funding_rate": record.get("funding_rate"),
        "open_interest": record.get("open_interest"),
        "raw": dict(record),
    }
    if normalized["bid"] is not None and normalized["ask"] is not None:
        normalized["mid"] = (normalized["bid"] + normalized["ask"]) / 2
    else:
        normalized["mid"] = None
    return normalized


def normalize_records(records: list[Mapping[str, Any]], *, venue: str, symbol: str) -> list[dict[str, Any]]:
    """Normalize records and order them by UTC timestamp."""
    return sorted(
        (normalize_record(item, venue=venue, symbol=symbol) for item in records),
        key=lambda item: item["timestamp"],
    )
