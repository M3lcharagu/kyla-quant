"""Opening-range breakout (ORB) setups in UTC."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Sequence

from .fvg import Bar


@dataclass(frozen=True)
class ORBConfig:
    range_minutes: int = 15
    london_open_utc: time = time(9, 0)
    new_york_open_utc: time = time(14, 30)
    max_hold_minutes: int = 45
    end_session_minutes: int = 60
    target_rr: float = 1.0
    retest: bool = False


@dataclass(frozen=True)
class ORBSetup:
    session: str
    session_date: object
    formed_index: int
    formed_at: object
    direction: str
    range_high: float
    range_low: float
    entry: float
    stop: float
    target: float
    latest_exit: object
    retest: bool = False


def _utc(value: object) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            from pandas import Timestamp
            dt = Timestamp(value).to_pydatetime()
        except Exception as exc:
            raise ValueError("ORB bars require parseable timestamps") from exc
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def detect_orb_setups(bars: Sequence[Bar], config: ORBConfig = ORBConfig()) -> list[ORBSetup]:
    """Detect first post-range break for London and NY on every UTC date.

    A breakout is confirmed by a bar high above range high or low below range
    low.  If ``retest`` is true, the entry is the first later touch of the
    broken edge; otherwise entry is the breakout close.  The stop is always the
    opposite side of the opening range and the latest exit is capped at both
    max-hold and session end.
    """
    if config.range_minutes <= 0 or config.max_hold_minutes <= 0:
        raise ValueError("ORB durations must be positive")
    groups: dict[tuple[object, str], list[int]] = {}
    for i, bar in enumerate(bars):
        dt = _utc(bar.timestamp)
        for name, open_time in (("london", config.london_open_utc), ("new_york", config.new_york_open_utc)):
            if dt.date() == dt.date():
                groups.setdefault((dt.date(), name), []).append(i)
    out: list[ORBSetup] = []
    for (date, name), indices in groups.items():
        open_time = config.london_open_utc if name == "london" else config.new_york_open_utc
        start = datetime.combine(date, open_time, tzinfo=timezone.utc)
        end_range = start + timedelta(minutes=config.range_minutes)
        range_indices = [i for i in indices if start <= _utc(bars[i].timestamp) < end_range]
        after = [i for i in indices if _utc(bars[i].timestamp) >= end_range]
        if not range_indices or not after:
            continue
        high = max(bars[i].high for i in range_indices)
        low = min(bars[i].low for i in range_indices)
        if high <= low:
            continue
        latest = min(start + timedelta(minutes=config.end_session_minutes),
                     start + timedelta(minutes=config.max_hold_minutes))
        for i in after:
            dt = _utc(bars[i].timestamp)
            if dt > latest:
                break
            bar = bars[i]
            direction = "long" if bar.high > high else "short" if bar.low < low else None
            if direction is None:
                continue
            entry = bar.close
            formed = i
            is_retest = False
            if config.retest:
                edge = high if direction == "long" else low
                for j in after[after.index(i) + 1:]:
                    if _utc(bars[j].timestamp) > latest:
                        break
                    if bars[j].low <= edge <= bars[j].high:
                        entry, formed, is_retest = edge, j, True
                        break
                if not is_retest:
                    continue
            risk = entry - low if direction == "long" else high - entry
            target = entry + config.target_rr * risk if direction == "long" else entry - config.target_rr * risk
            out.append(ORBSetup(name, date, formed, bars[formed].timestamp, direction,
                                high, low, entry, low if direction == "long" else high,
                                target, latest, is_retest))
            break
    return out
