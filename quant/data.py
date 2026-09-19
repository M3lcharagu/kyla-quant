"""Dependency-free data boundaries: Binance public klines, OANDA stub, CSV."""
import csv
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional

@dataclass(frozen=True)
class Candle:
    timestamp: Any
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None

def load_binance_klines(symbol: str, interval: str, *, start_time: Optional[int] = None,
                        end_time: Optional[int] = None, limit: int = 1000,
                        opener: Callable[..., Any] = urllib.request.urlopen) -> List[Candle]:
    """GET https://api.binance.com/api/v3/klines; public endpoint, no key.

    ``symbol`` is e.g. SOLUSDT, ``interval`` e.g. 5m, and times are optional
    Unix milliseconds. Binance caps a response at 1000 rows; paginate callers.
    """
    if not 1 <= limit <= 1000:
        raise ValueError("Binance limit must be between 1 and 1000")
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    if start_time is not None: params["startTime"] = start_time
    if end_time is not None: params["endTime"] = end_time
    url = "https://api.binance.com/api/v3/klines?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "kyla-quant/0.1"})
    with opener(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if isinstance(payload, dict) and payload.get("code"):
        raise RuntimeError("Binance returned an error: {}".format(payload))
    return [Candle(datetime.fromtimestamp(float(row[0]) / 1000, tz=timezone.utc),
        float(row[1]), float(row[2]), float(row[3]), float(row[4]),
        float(row[5]) if len(row) > 5 else None) for row in payload]

def load_oanda_candles(*, instrument: str, granularity: str, token: Optional[str] = None,
                        practice: bool = True, **_: Any) -> List[Candle]:
    """Stub for practice API.

    Practice endpoint: https://api-fxpractice.oanda.com/v3/instruments/{instrument}/candles
    with Authorization: Bearer <token>. Mel must create a practice API token.
    No token is invented or stored here; live mode is unsupported in v0.1.
    """
    if not practice: raise NotImplementedError("live OANDA loading is unsupported in v0.1")
    if not token: raise RuntimeError("OANDA practice API token required; Mel must create one")
    raise NotImplementedError("OANDA practice candle adapter remains a stub")

def load_local_csv(path: str) -> List[Candle]:
    """CSV fallback; requires timestamp/time/date and open,high,low,close headers."""
    with open(path, "r", newline="", encoding="utf-8") as handle:
        candles = []
        for row in csv.DictReader(handle):
            timestamp = row.get("timestamp") or row.get("time") or row.get("date")
            if timestamp is None: raise ValueError("CSV needs timestamp, time, or date")
            candles.append(Candle(timestamp, float(row["open"]), float(row["high"]),
                float(row["low"]), float(row["close"]),
                float(row["volume"]) if row.get("volume") not in (None, "") else None))
    return candles

local_csv_fallback = load_local_csv
