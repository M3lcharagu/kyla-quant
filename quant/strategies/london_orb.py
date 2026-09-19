"""GBPUSD London opening-range breakout strategy skeleton.

This module intentionally contains a small, dependency-free strategy that can be
passed directly to ``quant.backtest.Backtester``.  It is a research scaffold,
not a claim of profitability or a production trading system.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any, Mapping, Optional


class LondonORBStrategy:
    """Trade the first close outside the Asian range for GBPUSD.

    Every default below is an INITIAL GUESS and requires out-of-sample,
    cost-aware validation.  None of the parameters or rules is proven.

    The strategy expects completed candles whose timestamps are UTC (or include
    a timezone offset).  It is intended for 5- or 15-minute GBPUSD data and
    returns mappings understood by ``quant.backtest.Backtester``.

    Parameters are deliberately explicit so an experiment can record them:

    ``instrument``
        INITIAL GUESS: ``"GBPUSD"``; this is metadata only and does not filter
        candles.
    ``timeframe_minutes``
        INITIAL GUESS: 5 minutes; 15 minutes is also intended.  Other values
        are rejected rather than silently changing the experiment.
    ``asian_start_utc`` / ``asian_end_utc``
        INITIAL GUESS: 00:00 inclusive through 07:00 exclusive UTC.
    ``entry_start_utc`` / ``entry_end_utc``
        INITIAL GUESS: accept a breakout candle close from 07:00 inclusive
        through 11:00 exclusive UTC.
    ``stop_buffer``
        INITIAL GUESS: 0.00010 price units beyond the opposite range extreme;
        validate against GBPUSD precision, spread, and volatility.
    ``target_r``
        INITIAL GUESS: fixed 2R target; validate rather than treating it as
        an established edge.
    """

    def __init__(
        self,
        instrument: str = "GBPUSD",
        timeframe_minutes: int = 5,
        asian_start_utc: time = time(0, 0),
        asian_end_utc: time = time(7, 0),
        entry_start_utc: time = time(7, 0),
        entry_end_utc: time = time(11, 0),
        stop_buffer: float = 0.00010,
        target_r: float = 2.0,
    ) -> None:
        # All defaults are initial guesses requiring validation, not proven
        # parameters.  Keep this class stateful so it can be used as a stream
        # strategy by quant.backtest.Backtester.
        if timeframe_minutes not in (5, 15):
            raise ValueError("timeframe_minutes must be the intended 5 or 15")
        if asian_start_utc >= asian_end_utc:
            raise ValueError("Asian range must have a positive UTC window")
        if entry_start_utc >= entry_end_utc:
            raise ValueError("entry window must have a positive UTC window")
        if entry_start_utc < asian_end_utc:
            raise ValueError("entry window must start after the Asian range")
        if stop_buffer < 0.0:
            raise ValueError("stop_buffer cannot be negative")
        if target_r <= 0.0:
            raise ValueError("target_r must be positive")

        self.instrument = instrument
        self.timeframe_minutes = timeframe_minutes
        self.asian_start_utc = asian_start_utc
        self.asian_end_utc = asian_end_utc
        self.entry_start_utc = entry_start_utc
        self.entry_end_utc = entry_end_utc
        self.stop_buffer = float(stop_buffer)
        self.target_r = float(target_r)

        self._session_date: Optional[date] = None
        self._range_high: Optional[float] = None
        self._range_low: Optional[float] = None
        self._traded_today = False

    def next(self, candle: Any) -> Mapping[str, Any]:
        """Consume one completed candle and return a backtester signal.

        A breakout is confirmed only by the candle close.  The entry price used
        by ``quant.backtest.Backtester`` is therefore that close.  When there
        is no signal, ``{"action": "hold"}`` is returned.
        """
        timestamp = _as_utc_datetime(_field(candle, "timestamp", "time", "date"))
        current_date = timestamp.date()
        current_time = timestamp.time().replace(tzinfo=None)
        if current_date != self._session_date:
            self._start_session(current_date)

        high = float(_field(candle, "high"))
        low = float(_field(candle, "low"))
        close = float(_field(candle, "close"))

        if self.asian_start_utc <= current_time < self.asian_end_utc:
            self._range_high = high if self._range_high is None else max(self._range_high, high)
            self._range_low = low if self._range_low is None else min(self._range_low, low)
            return {"action": "hold"}

        in_entry_window = self.entry_start_utc <= current_time < self.entry_end_utc
        if (
            not in_entry_window
            or self._traded_today
            or self._range_high is None
            or self._range_low is None
            or self._range_high <= self._range_low
        ):
            return {"action": "hold"}

        if close > self._range_high:
            side = "long"
            stop = self._range_low - self.stop_buffer
            risk = close - stop
            target = close + self.target_r * risk
        elif close < self._range_low:
            side = "short"
            stop = self._range_high + self.stop_buffer
            risk = stop - close
            target = close - self.target_r * risk
        else:
            return {"action": "hold"}

        if risk <= 0.0:
            return {"action": "hold"}

        self._traded_today = True
        return {
            "action": "enter",
            "side": side,
            "stop": stop,
            "target": target,
        }

    def _start_session(self, session_date: date) -> None:
        self._session_date = session_date
        self._range_high = None
        self._range_low = None
        self._traded_today = False


def _field(value: Any, *names: str) -> Any:
    """Read a Candle-like object or mapping without external dependencies."""
    for name in names:
        if isinstance(value, Mapping) and name in value:
            return value[name]
        if hasattr(value, name):
            return getattr(value, name)
    joined = ", ".join(names)
    raise AttributeError("candle is missing one of: " + joined)


def _as_utc_datetime(value: Any) -> datetime:
    """Parse datetime-like timestamps using only the Python standard library."""
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, time())
    else:
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)

    if parsed.tzinfo is None:
        # Naive timestamps are an explicit UTC assumption for this skeleton.
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


# Short alias for callers that prefer the strategy name without the suffix.
LondonORB = LondonORBStrategy

__all__ = ["LondonORB", "LondonORBStrategy"]
