"""Key-free public OHLCV adapters with bounded pagination and validation."""
from __future__ import annotations

import csv
import io
import json
import logging
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional

LOGGER = logging.getLogger(__name__)

BINANCE_SPOT_URL = "https://api.binance.com/api/v3/klines"
BYBIT_SPOT_URL = "https://api.bybit.com/v5/market/kline"
OKX_CANDLES_URL = "https://www.okx.com/api/v5/market/candles"
GATE_SPOT_URL = "https://api.gateio.ws/api/v4/spot/candlesticks"
KUCOIN_URL = "https://api.kucoin.com/api/v1/market/candles"
MEXC_URL = "https://api.mexc.com/api/v3/klines"
BITFINEX_URL = "https://api-pub.bitfinex.com/v2/candles"
BITSTAMP_URL = "https://www.bitstamp.net/api/v2/ohlc"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
STOOQ_CSV_URL = "https://stooq.com/q/d/l/"

# Keep the repository's deliberately unverified public-data opener, but identify
# every outbound request as a normal browser request so public endpoints do not
# reject urllib's default user agent.
_SSL = ssl._create_unverified_context()
_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
urlopen = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=_SSL)
).open


@dataclass(frozen=True)
class Candle:
    timestamp: Any
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


def _ms(value: Any) -> int:
    """Normalize seconds or milliseconds to integer milliseconds."""
    number = float(value)
    return int(number if number >= 10_000_000_000 else number * 1000)


def _iso(milliseconds: int) -> str:
    return datetime.fromtimestamp(milliseconds / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _request_bytes(url: str, params: dict[str, Any]) -> bytes:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url + ("&" if "?" in url else "?") + query,
        headers={"User-Agent": _BROWSER_USER_AGENT, "Accept": "*/*"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", "replace")[:240]
        except Exception:
            detail = ""
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc


def _request_json(url: str, params: dict[str, Any]) -> Any:
    return json.loads(_request_bytes(url, params).decode("utf-8"))


def _candle(
    row: Any,
    indexes: tuple[int, int, int, int, int, int],
    milliseconds: bool = True,
) -> Candle:
    if not isinstance(row, (list, tuple)) or len(row) <= max(indexes):
        raise ValueError("malformed OHLCV row")
    ti, oi, hi, li, ci, vi = indexes
    timestamp = _iso(_ms(row[ti])) if milliseconds else _iso(int(float(row[ti]) * 1000))
    return Candle(
        timestamp,
        float(row[oi]),
        float(row[hi]),
        float(row[li]),
        float(row[ci]),
        None if row[vi] in (None, "") else float(row[vi]),
    )


def _validate(candles: List[Candle], requested: int, source: str) -> None:
    if not candles:
        raise ValueError(f"{source} returned no usable candles")
    previous = -1
    for candle in candles:
        current = _ms(candle.timestamp)
        if current <= previous:
            raise ValueError(f"{source} timestamps are not strictly ascending")
        previous = current
        if any(price <= 0 for price in (candle.open, candle.high, candle.low, candle.close)) or (
            candle.volume is not None and candle.volume < 0
        ):
            raise ValueError(f"{source} returned invalid OHLCV values")
        if candle.high < max(candle.open, candle.close, candle.low) or candle.low > min(
            candle.open, candle.close, candle.high
        ):
            raise ValueError(f"{source} returned inconsistent OHLC")
    if len(candles) < min(requested, 50):
        LOGGER.warning("%s supplied only %d/%d requested candles", source, len(candles), requested)


def _dedupe(rows: List[Candle]) -> List[Candle]:
    return [dict((_ms(c.timestamp), c) for c in rows)[key] for key in sorted(dict((_ms(c.timestamp), c) for c in rows))]


def _interval_seconds(interval: str) -> int:
    value = interval.lower().strip()
    if value.isdigit():
        return int(value) * 60
    if value.endswith("mo"):
        return int(value[:-2]) * 30 * 86400
    units = {"m": 60, "h": 3600, "d": 86400, "w": 604800}
    for suffix, multiplier in units.items():
        if value.endswith(suffix):
            return int(value[:-1]) * multiplier
    raise ValueError(f"unsupported interval: {interval}")


def _binance_interval(interval: str) -> str:
    return interval.lower()


def _bybit_interval(interval: str) -> str:
    return interval.lower().replace("h", "h").replace("d", "d")


def _okx_interval(interval: str) -> str:
    value = interval.lower()
    return {"1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1H", "2h": "2H", "4h": "4H", "6h": "6H", "12h": "12H", "1d": "1D", "1w": "1W"}.get(value, value)


def _compact(symbol: str) -> str:
    return symbol.upper().replace("/", "").replace("-", "").replace("_", "")


def _quote_symbol(symbol: str, quote: str = "USDT") -> str:
    compact = _compact(symbol)
    return compact if compact.endswith(quote) else compact + quote


def _fetch_binance(symbol: str, interval: str, limit: int, start: Optional[int], end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    out: List[Candle] = []
    cursor = end
    for _ in range(20):
        if len(out) >= limit:
            break
        n = min(1000, limit - len(out))
        params: dict[str, Any] = {"symbol": _quote_symbol(symbol), "interval": _binance_interval(interval), "limit": n}
        if start is not None:
            params["startTime"] = start
        if cursor is not None:
            params["endTime"] = cursor
        payload = _request_json(BINANCE_SPOT_URL, params)
        if not isinstance(payload, list):
            raise ValueError("Binance response was not a list")
        page = [_candle(row, (0, 1, 2, 3, 4, 5)) for row in payload]
        if not page:
            break
        out.extend(page)
        oldest = min(_ms(c.timestamp) for c in page)
        if start is not None or len(page) < n:
            break
        cursor = oldest - 1
        time.sleep(0.05)
    return _dedupe(out)[-limit:]


def _fetch_bybit(symbol: str, interval: str, limit: int, start: Optional[int], end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    out: List[Candle] = []
    cursor = end
    for _ in range(20):
        n = min(1000, limit - len(out))
        params: dict[str, Any] = {"category": "spot", "symbol": _quote_symbol(symbol), "interval": _bybit_interval(interval), "limit": n}
        if start is not None:
            params["start"] = start
        if cursor is not None:
            params["end"] = cursor
        payload = _request_json(BYBIT_SPOT_URL, params)
        result = payload.get("result") if isinstance(payload, dict) else None
        rows = result.get("list") if isinstance(result, dict) else None
        if not isinstance(rows, list):
            raise ValueError("Bybit response missing result.list")
        page = [_candle(row, (0, 1, 2, 3, 4, 5)) for row in rows]
        out.extend(page)
        if not page or start is not None or len(page) < n:
            break
        cursor = min(_ms(c.timestamp) for c in page) - 1
    return _dedupe(out)[-limit:]


def _okx_candle(row: Any) -> Candle:
    if not isinstance(row, (list, tuple)) or len(row) < 6:
        raise ValueError("malformed OKX OHLCV row")
    ts_ms = int(row[0])
    timestamp = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    return Candle(timestamp, float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]) if row[5] not in (None, "") else None)


def _fetch_okx(symbol: str, interval: str, limit: int, start: Optional[int], end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    out: List[Candle] = []
    after = end + 1 if end is not None else None
    previous_after: Optional[int] = None
    # OKX v5 pages at most 300 candles. Walk backwards with `after` equal to
    # the oldest timestamp in the last page, up to 20,000 candles, then reverse.
    while len(out) < 20_000:
        n = min(300, 20_000 - len(out))
        params: dict[str, Any] = {"instId": _compact(symbol).replace("USDT", "-USDT"), "bar": _okx_interval(interval), "limit": n}
        if after is not None:
            params["after"] = str(int(after))
        payload = _request_json(OKX_CANDLES_URL, params)
        rows = payload.get("data") if isinstance(payload, dict) and payload.get("code") == "0" else None
        if not isinstance(rows, list):
            raise ValueError("OKX response missing data")
        page = [_okx_candle(row) for row in rows]
        if not page:
            break
        out.extend(page)
        oldest_ms = min(int(row[0]) for row in rows)
        if previous_after is not None and oldest_ms >= previous_after:
            break
        if start is not None and oldest_ms <= start:
            break
        if len(page) < n:
            break
        previous_after = after
        after = oldest_ms
        time.sleep(0.05)
    rows = list(reversed(_dedupe(out)))
    return rows[-limit:]


def _fetch_gate(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    payload = _request_json(GATE_SPOT_URL, {"currency_pair": "SOL_USDT", "interval": "5m", "limit": min(limit, 1000)})
    if not isinstance(payload, list):
        raise ValueError("Gate.io response was not a list")
    return [_candle(row, (0, 5, 3, 4, 2, 1)) for row in reversed(payload)]


def _fetch_kucoin(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    payload = _request_json(KUCOIN_URL, {"symbol": "SOL-USDT", "type": "5min"})
    rows = payload.get("data") if isinstance(payload, dict) and payload.get("code") == "200000" else None
    if not isinstance(rows, list):
        raise ValueError("KuCoin response missing data")
    return [_candle(row, (0, 1, 2, 3, 4, 5), milliseconds=False) for row in rows[-min(limit, 1500):]]


def _fetch_mexc(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    payload = _request_json(MEXC_URL, {"symbol": "SOLUSDT", "interval": "5m", "limit": min(limit, 1000)})
    if not isinstance(payload, list):
        raise ValueError("MEXC response was not a list")
    return [_candle(row, (0, 1, 2, 3, 4, 5)) for row in payload]


def _fetch_bitfinex(limit: int, end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    out: List[Candle] = []
    cursor = end
    for _ in range(20):
        n = min(1000, limit - len(out))
        params = {"limit": n, "sort": 1}
        if cursor is not None:
            params["end"] = cursor
        payload = _request_json(f"{BITFINEX_URL}/trade:5m:tSOLUSD/hist", params)
        if not isinstance(payload, list):
            raise ValueError("Bitfinex response was not a list")
        page = [_candle(row, (0, 2, 3, 4, 1, 5)) for row in payload]
        out.extend(page)
        if not page or len(page) < n:
            break
        cursor = min(_ms(c.timestamp) for c in page) - 1
    return _dedupe(out)[-limit:]


def _fetch_bitstamp(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    payload = _request_json(f"{BITSTAMP_URL}/solusd/", {"step": 300, "limit": min(limit, 1000)})
    rows = payload.get("data", {}).get("ohlc") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("Bitstamp response missing data.ohlc")
    return [Candle(_iso(int(float(row["timestamp"]) * 1000)), float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), float(row.get("volume", 0))) for row in rows]


def _fetch_yahoo(symbol: str, limit: int, opener: Callable[..., Any]) -> List[Candle]:
    yahoo_symbol = f"{_compact(symbol).upper()}-USD"
    url = YAHOO_CHART_URL + urllib.parse.quote(yahoo_symbol, safe="")
    payload = _request_json(url, {"interval": "5m", "range": "60d"})
    result = payload.get("chart", {}).get("result") if isinstance(payload, dict) else None
    chart = result[0] if isinstance(result, list) and result else None
    timestamps = chart.get("timestamp") if isinstance(chart, dict) else None
    quote = chart.get("indicators", {}).get("quote", [{}])[0] if isinstance(chart, dict) else {}
    if not isinstance(timestamps, list) or not isinstance(quote, dict):
        raise ValueError("Yahoo response missing chart arrays")
    rows: List[Candle] = []
    for index, timestamp in enumerate(timestamps):
        values = [quote.get(field, [None] * len(timestamps))[index] for field in ("open", "high", "low", "close", "volume")]
        if any(value is None for value in values[:4]):
            continue
        rows.append(Candle(_iso(int(timestamp) * 1000), float(values[0]), float(values[1]), float(values[2]), float(values[3]), None if values[4] is None else float(values[4])))
    return _dedupe(rows)[-limit:]


def _fetch_stooq(symbol: str, limit: int, opener: Callable[..., Any]) -> List[Candle]:
    stooq_symbol = f"{_compact(symbol).lower()}usd"
    payload = _request_bytes(STOOQ_CSV_URL, {"s": stooq_symbol, "i": "300"}).decode("utf-8", "replace")
    rows = csv.DictReader(io.StringIO(payload))
    candles: List[Candle] = []
    for row in rows:
        date_value = (row.get("Date") or row.get("date") or "").strip()
        time_value = (row.get("Time") or row.get("time") or "").strip()
        if not date_value:
            continue
        timestamp_text = f"{date_value}T{time_value}" if time_value else date_value
        try:
            parsed = datetime.fromisoformat(timestamp_text).replace(tzinfo=timezone.utc)
            values = [row.get(field) for field in ("Open", "High", "Low", "Close", "Volume")]
            if any(value in (None, "", "N/D", "null") for value in values[:4]):
                continue
            candles.append(Candle(parsed.isoformat().replace("+00:00", "Z"), float(values[0]), float(values[1]), float(values[2]), float(values[3]), None if values[4] in (None, "", "N/D", "null") else float(values[4])))
        except (TypeError, ValueError):
            continue
    return _dedupe(candles)[-limit:]


def load_binance_candles(
    symbol: str,
    interval: str,
    *,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    limit: int = 1000,
    opener: Callable[..., Any] = urlopen,
) -> List[Candle]:
    """Load ascending, validated, key-free public candles with fallbacks."""
    if limit < 1:
        raise ValueError("limit must be positive")
    errors: List[str] = []
    sources: list[tuple[str, Callable[[], List[Candle]]]] = [
        ("Binance spot", lambda: _fetch_binance(symbol, interval, limit, start_time, end_time, opener)),
        ("Bybit spot", lambda: _fetch_bybit(symbol, interval, limit, start_time, end_time, opener)),
        ("OKX", lambda: _fetch_okx(symbol, interval, limit, start_time, end_time, opener)),
    ]
    if _compact(symbol) == "SOLUSDT" and interval.lower() in ("5m", "5"):
        sources += [
            ("Gate.io spot", lambda: _fetch_gate(limit, opener)),
            ("KuCoin", lambda: _fetch_kucoin(limit, opener)),
            ("MEXC", lambda: _fetch_mexc(limit, opener)),
            ("Bitfinex", lambda: _fetch_bitfinex(limit, end_time, opener)),
            ("Bitstamp", lambda: _fetch_bitstamp(limit, opener)),
        ]
    sources += [
        ("Yahoo Finance chart", lambda: _fetch_yahoo(symbol, limit, opener)),
        ("Stooq CSV", lambda: _fetch_stooq(symbol, limit, opener)),
    ]
    for name, loader in sources:
        try:
            rows = _dedupe(loader())
            _validate(rows, limit, name)
            LOGGER.info("data source succeeded: %s (%d candles)", name, len(rows))
            return rows[-limit:]
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            LOGGER.warning("data source failed: %s", errors[-1])
    raise RuntimeError("all public data sources failed: " + "; ".join(errors))


load_binance_klines = load_binance_candles


def load_local_csv(path: str) -> List[Candle]:
    with open(path, "r", newline="", encoding="utf-8") as handle:
        output: List[Candle] = []
        for row in csv.DictReader(handle):
            timestamp = row.get("timestamp") or row.get("time") or row.get("date")
            output.append(Candle(timestamp, float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), None if row.get("volume") in (None, "") else float(row["volume"])))
    _validate(output, len(output), "CSV")
    return _dedupe(output)


def load_oanda_candles(*, instrument: str, granularity: str, token: Optional[str] = None, practice: bool = True, **_: Any) -> List[Candle]:
    raise NotImplementedError("live OANDA loading requires an explicitly supplied token")


local_csv_fallback = load_local_csv
