"""Key-free public OHLCV adapters with bounded pagination and safe parsing."""
from __future__ import annotations

import csv
import io
import json
import logging
import math
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
KRAKEN_OHLC_URL = "https://api.kraken.com/0/public/OHLC"
COINBASE_CANDLES_URL = "https://api.exchange.coinbase.com/products"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
STOOQ_CSV_URL = "https://stooq.com/q/d/l/"
_SSL = ssl._create_unverified_context()
_BROWSER_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
urlopen = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_SSL)).open


@dataclass(frozen=True)
class Candle:
    timestamp: Any
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


class DataSourceError(RuntimeError):
    """An upstream error retaining the HTTP status and response excerpt for reports."""
    def __init__(self, message: str, *, status: Optional[int] = None, excerpt: str = "", url: str = ""):
        super().__init__(message)
        self.http_status = status
        self.response_excerpt = excerpt[:200]
        self.url = url


_LAST_PARSE_STATS: dict[str, dict[str, Any]] = {}


def normalize_timestamp(value: Any, time_value: Any = None) -> str:
    """Normalize epoch seconds/milliseconds, ISO-8601 (including Z), or date-only values."""
    if time_value not in (None, ""):
        value = f"{str(value).strip()}T{str(time_value).strip()}"
    if isinstance(value, bool) or value is None:
        raise ValueError(f"invalid timestamp: {value!r}")
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"invalid timestamp: {value!r}")
        if number > 1_000_000_000_000:
            number /= 1000.0
        dt = datetime.fromtimestamp(number, tz=timezone.utc)
    else:
        text = str(value).strip()
        if not text:
            raise ValueError("empty timestamp")
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _normalize_timestamp(value: Any, time_value: Any = None) -> str:
    return normalize_timestamp(value, time_value)


def _ms(value: Any) -> int:
    return int(datetime.fromisoformat(normalize_timestamp(value).replace("Z", "+00:00")).timestamp() * 1000)


def _iso(ms: int) -> str:
    return normalize_timestamp(ms)


def _compact(symbol: str) -> str:
    return symbol.upper().replace("/", "").replace("-", "").replace("_", "")


def _asset(symbol: str) -> str:
    compact = _compact(symbol)
    for suffix in ("USDT", "USDC", "USD"):
        if compact.endswith(suffix):
            return compact[:-len(suffix)]
    return compact


def _quote(symbol: str) -> str:
    compact = _compact(symbol)
    return compact if compact.endswith(("USDT", "USDC", "USD")) else compact + "USDT"


def _request_bytes(url: str, params: dict[str, Any]) -> bytes:
    query = urllib.parse.urlencode(params)
    full_url = url + ("?" + query if query else "")
    req = urllib.request.Request(full_url, headers={"User-Agent": _BROWSER_USER_AGENT, "Accept": "*/*"})
    try:
        with urlopen(req, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        try:
            excerpt = exc.read().decode("utf-8", "replace")[:200]
        except Exception:
            excerpt = ""
        raise DataSourceError(f"HTTP {exc.code} from {full_url}: {excerpt}", status=exc.code, excerpt=excerpt, url=full_url) from exc
    except Exception as exc:
        raise DataSourceError(f"request failed for {full_url}: {exc}", url=full_url) from exc


def _request_json(url: str, params: dict[str, Any]) -> Any:
    body = _request_bytes(url, params)
    try:
        return json.loads(body.decode("utf-8"))
    except Exception as exc:
        excerpt = body[:200].decode("utf-8", "replace")
        raise DataSourceError(f"invalid JSON from {url}: {excerpt}", excerpt=excerpt, url=url) from exc


_LAST_PARSE_STATS: dict[str, dict[str, Any]] = {}


def _record(source: str, skipped: int, count: int) -> None:
    _LAST_PARSE_STATS[source] = {"skipped": skipped, "candles": count, "status": "SUCCESS"}


def source_stats(source: str) -> dict[str, Any]:
    wanted = source.lower()
    for name, stats in reversed(list(_LAST_PARSE_STATS.items())):
        if name.lower() == wanted or wanted in name.lower() or name.lower() in wanted:
            return dict(stats)
    return {"skipped": 0, "candles": 0}


def _dedupe(rows: List[Candle]) -> List[Candle]:
    unique = {_ms(c.timestamp): c for c in rows}
    return [unique[key] for key in sorted(unique)]


def _row(row: Any, idx: tuple[Any, Any, Any, Any, Any]) -> Candle:
    ti, oi, hi, li, ci = idx
    timestamp = normalize_timestamp(row[ti] if isinstance(ti, int) else row[ti])
    values = [float(row[oi]), float(row[hi]), float(row[li]), float(row[ci])]
    if any(not math.isfinite(value) for value in values):
        raise ValueError("non-finite OHLC")
    volume = None
    if len(row) > 5 and row[5] not in (None, ""):
        volume = float(row[5])
        if not math.isfinite(volume):
            raise ValueError("non-finite volume")
    return Candle(timestamp, values[0], values[1], values[2], values[3], volume)


def _parsed(source: str, rows: Any, idx: tuple[Any, Any, Any, Any, Any], limit: int, reverse: bool = False) -> List[Candle]:
    out: List[Candle] = []
    skipped = 0
    for raw in (reversed(rows) if reverse else rows):
        try:
            out.append(_row(raw, idx))
        except (TypeError, ValueError, IndexError, KeyError):
            skipped += 1
    result = _dedupe(out)
    _record(source, skipped, len(result))
    return result[-limit:] if limit else result


def _validate(rows: List[Candle], requested: int, source: str) -> None:
    if not rows:
        raise ValueError(f"{source} returned no usable candles")
    previous = -1
    for candle in rows:
        stamp = _ms(candle.timestamp)
        if stamp <= previous:
            raise ValueError(f"{source} timestamps are not strictly ascending")
        previous = stamp
        if any(value <= 0 for value in (candle.open, candle.high, candle.low, candle.close)):
            raise ValueError(f"{source} returned invalid OHLC values")
        if candle.high < max(candle.open, candle.close, candle.low) or candle.low > min(candle.open, candle.close, candle.high):
            raise ValueError(f"{source} returned inconsistent OHLC")
        if candle.volume is not None and candle.volume < 0:
            raise ValueError(f"{source} returned negative volume")
    if len(rows) < min(requested, 50):
        LOGGER.warning("%s supplied only %d/%d requested candles", source, len(rows), requested)


def _fetch_simple(url: str, params: dict[str, Any], source: str, idx: tuple[Any, Any, Any, Any, Any], limit: int, rows_key: Optional[str] = None) -> List[Candle]:
    data = _request_json(url, params)
    rows = data.get(rows_key) if rows_key and isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError(f"{source} response missing rows")
    return _parsed(source, rows, idx, limit)


def _fetch_binance(symbol: str, interval: str, limit: int, start: Optional[int], end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    out: List[Candle] = []; cursor = start; skipped = 0
    for _ in range(20):
        n = min(1000, limit - len(out))
        if n <= 0: break
        params: dict[str, Any] = {"symbol": _quote(symbol), "interval": interval, "limit": n}
        if cursor is not None: params["startTime"] = cursor
        if end is not None: params["endTime"] = end
        data = _request_json(BINANCE_SPOT_URL, params)
        if not isinstance(data, list): raise ValueError("Binance response was not a list")
        page = _parsed("Binance spot", data, (0, 1, 2, 3, 4), n); skipped += source_stats("Binance spot").get("skipped", 0)
        if not page: break
        out += page; cursor = max(_ms(c.timestamp) for c in page) + 1
        if len(page) < n: break
        time.sleep(0.05)
    result = _dedupe(out); _record("Binance spot", skipped, len(result)); return result[-limit:]


def _fetch_bybit(symbol: str, interval: str, limit: int, start: Optional[int], end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    out: List[Candle] = []; cursor = end; skipped = 0
    for _ in range(20):
        n = min(1000, limit - len(out))
        if n <= 0: break
        params: dict[str, Any] = {"category": "spot", "symbol": _quote(symbol), "interval": interval.lower().replace("m", ""), "limit": n}
        if start is not None: params["start"] = start
        if cursor is not None: params["end"] = cursor
        payload = _request_json(BYBIT_SPOT_URL, params); result = payload.get("result", {}) if isinstance(payload, dict) else {}
        rows = result.get("list") if isinstance(result, dict) else None
        if not isinstance(rows, list): raise ValueError("Bybit response missing result.list")
        page = _parsed("Bybit spot", rows, (0, 1, 2, 3, 4), n, True); skipped += source_stats("Bybit spot").get("skipped", 0)
        if not page: break
        out += page; oldest = min(_ms(c.timestamp) for c in page); cursor = oldest - 1
        if len(page) < n or (start is not None and oldest <= start): break
    result = _dedupe(out); _record("Bybit spot", skipped, len(result)); return result[-limit:]


def _fetch_okx(symbol: str, interval: str, limit: int, start: Optional[int], end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    asset = _asset(symbol); quote = "USDT" if _compact(symbol).endswith("USDT") else "USD"
    params = {"instId": f"{asset}-{quote}", "bar": interval, "limit": min(limit, 300)}
    data = _request_json(OKX_CANDLES_URL, params); rows = data.get("data") if isinstance(data, dict) and data.get("code") == "0" else None
    if not isinstance(rows, list): raise ValueError("OKX response missing data")
    return _parsed("OKX", rows, (0, 3, 2, 1, 4), limit, True)


def _fetch_kraken(symbol: str, limit: int, opener: Callable[..., Any]) -> List[Candle]:
    pair = {"BTC": "XBTUSD"}.get(_asset(symbol), _asset(symbol) + "USD")
    target = min(max(limit, 720), 20000); since = int(time.time()) - target * 300
    out: List[Candle] = []; skipped = 0
    for _ in range(40):
        if len(out) >= min(limit, 20000): break
        payload = _request_json(KRAKEN_OHLC_URL, {"pair": pair, "interval": 5, "since": since})
        if not isinstance(payload, dict) or payload.get("error"):
            raise ValueError(f"Kraken response error: {payload.get('error') if isinstance(payload, dict) else payload}")
        result = payload.get("result", {}); rows = next((value for key, value in result.items() if key != "last" and isinstance(value, list)), None) if isinstance(result, dict) else None
        if not isinstance(rows, list): raise ValueError("Kraken response missing OHLC rows")
        page = _parsed("Kraken OHLC", rows, (0, 1, 2, 3, 4), 20000); skipped += source_stats("Kraken OHLC").get("skipped", 0)
        if not page: break
        out += page; since = max(_ms(c.timestamp) for c in page) // 1000 + 300
        if len(page) < 2: break
        time.sleep(0.05)
    result = _dedupe(out); _record("Kraken OHLC", skipped, len(result)); return result[-min(limit, 20000):]


def _fetch_coinbase(symbol: str, limit: int, opener: Callable[..., Any]) -> List[Candle]:
    product = f"{_asset(symbol)}-USD"; end = int(time.time() * 1000); window = 300 * 300 * 1000
    out: List[Candle] = []; skipped = 0
    for _ in range(67):
        if len(out) >= min(limit, 20000): break
        start = end - window
        data = _request_json(f"{COINBASE_CANDLES_URL}/{product}/candles", {"granularity": 300, "start": _iso(start), "end": _iso(end)})
        if not isinstance(data, list): raise ValueError("Coinbase candles response was not a list")
        page = _parsed("Coinbase candles", data, (0, 3, 2, 1, 4), 300); skipped += source_stats("Coinbase candles").get("skipped", 0)
        if not page: break
        out += page; end = min(_ms(c.timestamp) for c in page) - 1
        if len(page) < 300: break
        time.sleep(0.05)
    result = _dedupe(out); _record("Coinbase candles", skipped, len(result)); return result[-min(limit, 20000):]


def _fetch_yahoo(symbol: str, limit: int, opener: Callable[..., Any]) -> List[Candle]:
    sym = f"{_asset(symbol).upper()}-USD"
    payload = _request_json(YAHOO_CHART_URL + urllib.parse.quote(sym, safe=""), {"interval": "5m", "range": "1mo"})
    result = payload.get("chart", {}).get("result") if isinstance(payload, dict) else None; chart = result[0] if isinstance(result, list) and result else None
    if not isinstance(chart, dict): raise ValueError("Yahoo response missing chart result")
    timestamps = chart.get("timestamp"); quote = (chart.get("indicators", {}).get("quote") or [{}])[0]
    if not isinstance(timestamps, list) or not isinstance(quote, dict): raise ValueError("Yahoo response missing chart arrays")
    rows = []
    for i, stamp in enumerate(timestamps):
        try:
            vals = [quote[name][i] for name in ("open", "high", "low", "close", "volume")]
            if any(value is None for value in vals): raise ValueError("null Yahoo candle")
            rows.append([stamp, *vals])
        except (TypeError, IndexError, KeyError, ValueError):
            rows.append(["bad", 0, 0, 0, 0, 0])
    return _parsed("Yahoo Finance chart", rows, (0, 1, 2, 3, 4), limit)


def _fetch_stooq(symbol: str, limit: int, opener: Callable[..., Any]) -> List[Candle]:
    text = _request_bytes(STOOQ_CSV_URL, {"s": f"{_asset(symbol).lower()}usd", "i": "300"}).decode("utf-8", "replace")
    rows = []; skipped = 0
    for row in csv.DictReader(io.StringIO(text)):
        try:
            stamp = row.get("Date") or row.get("date") or row.get("Time") or row.get("time")
            rows.append([stamp, float(row["Open"]), float(row["High"]), float(row["Low"]), float(row["Close"]), float(row.get("Volume") or 0)])
        except (TypeError, ValueError, KeyError): skipped += 1
    parsed = _parsed("Stooq CSV", rows, (0, 1, 2, 3, 4), limit); stats = source_stats("Stooq CSV")
    _record("Stooq CSV", stats.get("skipped", 0) + skipped, len(parsed)); return parsed


def _fetch_gate(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    return _fetch_simple(GATE_SPOT_URL, {"currency_pair": "SOL_USDT", "interval": "5m", "limit": min(limit, 1000)}, "Gate.io spot", (0, 5, 4, 3, 2), limit)


def _fetch_kucoin(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    return _fetch_simple(KUCOIN_URL, {"symbol": "SOL-USDT", "type": "5min"}, "KuCoin", (0, 1, 2, 3, 4), limit, "data")


def _fetch_mexc(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    return _fetch_simple(MEXC_URL, {"symbol": "SOLUSDT", "interval": "5m", "limit": min(limit, 1000)}, "MEXC", (0, 1, 2, 3, 4), limit)


def _fetch_bitfinex(limit: int, end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    return _fetch_simple(f"{BITFINEX_URL}/trade:5m:tSOLUSD/hist", {"limit": min(limit, 1000), "sort": 1}, "Bitfinex", (0, 1, 2, 3, 4), limit)


def _fetch_bitstamp(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    data = _request_json(f"{BITSTAMP_URL}/solusd/", {"step": 300, "limit": min(limit, 1000)})
    rows = data.get("data", {}).get("ohlc", []) if isinstance(data, dict) else []
    if not isinstance(rows, list): raise ValueError("Bitstamp response missing data.ohlc")
    return _parsed("Bitstamp", rows, ("timestamp", "open", "high", "low", "close"), limit)


def load_binance_candles(symbol: str, interval: str, *, start_time: Optional[int] = None, end_time: Optional[int] = None, limit: int = 1000, opener: Callable[..., Any] = urlopen) -> List[Candle]:
    if limit < 1: raise ValueError("limit must be positive")
    sources: list[tuple[str, Callable[[], List[Candle]]]] = [
        ("Binance spot", lambda: _fetch_binance(symbol, interval, limit, start_time, end_time, opener)),
        ("Bybit spot", lambda: _fetch_bybit(symbol, interval, limit, start_time, end_time, opener)),
        ("OKX", lambda: _fetch_okx(symbol, interval, limit, start_time, end_time, opener)),
    ]
    if _compact(symbol) in ("SOLUSDT", "SOLUSD") and interval.lower() in ("5m", "5"):
        sources += [("Gate.io spot", lambda: _fetch_gate(limit, opener)), ("KuCoin", lambda: _fetch_kucoin(limit, opener)), ("MEXC", lambda: _fetch_mexc(limit, opener)), ("Bitfinex", lambda: _fetch_bitfinex(limit, end_time, opener)), ("Bitstamp", lambda: _fetch_bitstamp(limit, opener))]
    if interval.lower() in ("5m", "5"):
        sources += [("Kraken OHLC", lambda: _fetch_kraken(symbol, limit, opener)), ("Coinbase candles", lambda: _fetch_coinbase(symbol, limit, opener))]
    sources += [("Yahoo Finance chart", lambda: _fetch_yahoo(symbol, limit, opener)), ("Stooq CSV", lambda: _fetch_stooq(symbol, limit, opener))]
    errors = []
    for name, loader in sources:
        try:
            rows = _dedupe(loader()); _validate(rows, limit, name); return rows[-limit:]
        except Exception as exc:
            errors.append(f"{name}: {exc}"); LOGGER.warning("data source failed symbol=%s interval=%s source=%s: %s", symbol, interval, name, exc)
    raise RuntimeError("all public data sources failed: " + "; ".join(errors))


load_binance_klines = load_binance_candles


def load_local_csv(path: str) -> List[Candle]:
    rows: List[Candle] = []; skipped = 0
    with open(path, "r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                stamp = row.get("timestamp") or row.get("time") or row.get("date")
                rows.append(Candle(normalize_timestamp(stamp), float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), None if row.get("volume") in (None, "") else float(row["volume"])))
            except (TypeError, ValueError, KeyError): skipped += 1
    result = _dedupe(rows); _record("CSV", skipped, len(result)); _validate(result, len(result), "CSV"); return result


def load_oanda_candles(*, instrument: str, granularity: str, token: Optional[str] = None, practice: bool = True, **_: Any) -> List[Candle]:
    raise NotImplementedError("live OANDA loading requires an explicitly supplied token")


local_csv_fallback = load_local_csv
