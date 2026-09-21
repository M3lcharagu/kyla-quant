"""Dependency-free public candle adapters and CSV fallback."""
import csv
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional

LOGGER = logging.getLogger(__name__)
_BINANCE_SPOT_URL = "https://api.binance.com/api/v3/klines"
_BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"
_BYBIT_SPOT_URL = "https://api.bybit.com/v5/market/kline"
_OKX_CANDLES_URL = "https://www.okx.com/api/v5/market/candles"
_CRYPTOCOMPARE_URL = "https://min-api.cryptocompare.com/data/v2/histominute"
_COINBASE_URL = "https://api.exchange.coinbase.com/products/SOL-USD/candles"
_KRAKEN_URL = "https://api.kraken.com/0/public/OHLC"
_MIN_CANDLES = 1000
_SOL_PRICE_MIN = 50.0
_SOL_PRICE_MAX = 400.0

@dataclass(frozen=True)
class Candle:
    timestamp: Any
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None

def _utc_datetime(timestamp: Any, *, milliseconds: bool) -> datetime:
    value = float(timestamp) / (1000.0 if milliseconds else 1.0)
    return datetime.fromtimestamp(value, tz=timezone.utc)

def _ms(candle: Candle) -> int:
    return int(candle.timestamp.timestamp() * 1000)

def _iso(ms: int) -> str:
    return _utc_datetime(ms, milliseconds=True).isoformat().replace("+00:00", "Z")

def _request_json(url: str, params: dict, opener: Callable[..., Any]) -> Any:
    query = urllib.parse.urlencode(params)
    full_url = url + (("&" if "?" in url else "?") + query if query else "")
    request = urllib.request.Request(full_url, headers={"User-Agent": "kyla-quant/0.1"})
    try:
        with opener(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace").strip()[:240]
        except Exception:
            detail = ""
        raise RuntimeError(f"HTTP {exc.code} from {url}{(': ' + detail) if detail else ''}") from exc

def _row(row: Any, *, ms: bool, indexes: tuple) -> Candle:
    if not isinstance(row, (list, tuple)) or len(row) <= max(indexes):
        raise ValueError("exchange returned a malformed candle row")
    t, oi, hi, li, ci, vi = indexes
    return Candle(_utc_datetime(row[t], milliseconds=ms), float(row[oi]), float(row[hi]), float(row[li]), float(row[ci]), float(row[vi]))

def _normalise_binance(payload: Any) -> List[Candle]:
    if isinstance(payload, dict):
        raise RuntimeError(f"Binance returned an error: code={payload.get('code')!r}, message={payload.get('msg') or payload}")
    if not isinstance(payload, list):
        raise RuntimeError(f"Binance returned unexpected JSON: {type(payload).__name__}")
    return [_row(row, ms=True, indexes=(0, 1, 2, 3, 4, 5)) for row in payload]

def _normalise_bybit(payload: Any) -> List[Candle]:
    if not isinstance(payload, dict) or str(payload.get("retCode", "0")) != "0":
        raise RuntimeError(f"Bybit returned an error: {payload}")
    rows = (payload.get("result") or {}).get("list")
    if not isinstance(rows, list):
        raise RuntimeError("Bybit response did not contain result.list")
    return [_row(row, ms=True, indexes=(0, 1, 2, 3, 4, 5)) for row in rows]

def _normalise_okx(payload: Any) -> List[Candle]:
    if not isinstance(payload, dict) or str(payload.get("code", "0")) != "0":
        raise RuntimeError(f"OKX returned an error: {payload}")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise RuntimeError("OKX response did not contain data")
    return [_row(row, ms=True, indexes=(0, 1, 2, 3, 4, 5)) for row in rows]

def _normalise_cryptocompare(payload: Any) -> List[Candle]:
    if not isinstance(payload, dict) or payload.get("Response") != "Success":
        raise RuntimeError(f"CryptoCompare returned an error: {payload}")
    rows = (payload.get("Data") or {}).get("Data")
    if not isinstance(rows, list):
        raise RuntimeError("CryptoCompare response did not contain Data.Data")
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("CryptoCompare returned a malformed candle row")
        result.append(Candle(_utc_datetime(row["time"], milliseconds=False), float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), float(row.get("volumefrom") or row.get("volumeto"))))
    return result

def _normalise_coinbase(payload: Any) -> List[Candle]:
    if not isinstance(payload, list):
        raise RuntimeError("Coinbase returned unexpected JSON")
    # Coinbase: [time, low, high, open, close, volume].
    return [_row(row, ms=False, indexes=(0, 3, 2, 1, 4, 5)) for row in payload]

def _normalise_kraken(payload: Any) -> List[Candle]:
    if not isinstance(payload, dict):
        raise RuntimeError("Kraken returned unexpected JSON")
    if payload.get("error"):
        raise RuntimeError(f"Kraken returned an error: {payload['error']}")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("Kraken response did not contain result")
    rows = next((v for k, v in result.items() if k != "last"), None)
    if not isinstance(rows, list):
        raise RuntimeError("Kraken response did not contain an OHLC pair")
    return [_row(row, ms=False, indexes=(0, 1, 2, 3, 4, 6)) for row in rows]

def _dedupe_sort(candles: List[Candle]) -> List[Candle]:
    return [dict((_ms(c), c) for c in candles)[key] for key in sorted({_ms(c) for c in candles})]

def _validate_candidate(candles: List[Candle], requested: int, source: str) -> None:
    # A source may be exhausted below 1,000 rows; only unusable/empty data fails.
    if not candles:
        raise ValueError(f"{source} returned no usable candles")
    previous = None
    for candle in candles:
        if previous is not None and candle.timestamp <= previous:
            raise ValueError(f"{source} timestamps are not strictly ascending")
        previous = candle.timestamp
        if any(price < _SOL_PRICE_MIN or price > _SOL_PRICE_MAX for price in (candle.open, candle.high, candle.low, candle.close)):
            raise ValueError(f"{source} returned an implausible SOL price (expected {_SOL_PRICE_MIN:g}-{_SOL_PRICE_MAX:g})")
        if candle.volume is None or candle.volume <= 0:
            raise ValueError(f"{source} returned a candle with non-positive volume")

def _compact(symbol: str) -> str:
    return symbol.upper().replace("/", "").replace("-", "").replace("_", "")

def _bybit_symbol(symbol: str) -> str:
    return _compact(symbol)

def _okx_symbol(symbol: str) -> str:
    compact = _compact(symbol)
    for quote in ("USDT", "USDC", "USD"):
        if compact.endswith(quote):
            return compact[:-len(quote)] + "-" + quote
    return compact

def _kraken_symbol(symbol: str) -> str:
    compact = _compact(symbol)
    return compact[:-4] + "USD" if compact.endswith("USDT") else compact

def _bybit_interval(interval: str) -> str:
    return {"1m":"1", "3m":"3", "5m":"5", "15m":"15", "30m":"30", "1h":"60", "2h":"120", "4h":"240", "6h":"360", "12h":"720", "1d":"D", "1w":"W", "1mo":"M"}.get(interval.lower(), interval)

def _okx_interval(interval: str) -> str:
    return {"1h":"1H", "2h":"2H", "4h":"4H", "6h":"6H", "12h":"12H", "1d":"1D", "1w":"1W", "1mo":"1M"}.get(interval.lower(), interval)

def _interval_seconds(interval: str) -> int:
    value = interval.lower()
    if value.isdigit():
        return int(value) * 60
    if value.endswith("mo"):
        return int(value[:-2]) * 30 * 86400
    for suffix, multiplier in (("m", 60), ("h", 3600), ("d", 86400), ("w", 604800)):
        if value.endswith(suffix):
            return int(value[:-1]) * multiplier
    return 300

def _filter(candles: List[Candle], start: Optional[int], end: Optional[int]) -> List[Candle]:
    result = _dedupe_sort(candles)
    if start is not None:
        result = [c for c in result if _ms(c) >= start]
    if end is not None:
        result = [c for c in result if _ms(c) <= end]
    return result

def _fetch_back(url: str, params: dict, normalise: Callable[[Any], List[Candle]], page_size: int, requested: int, start: Optional[int], end: Optional[int], opener: Callable[..., Any], source: str, cursor_name: Optional[str] = None, cursor: Optional[int] = None) -> List[Candle]:
    collected: List[Candle] = []
    while len(_dedupe_sort(collected)) < requested:
        page_params = dict(params)
        page_params["limit"] = page_size
        if cursor_name and cursor is not None:
            page_params[cursor_name] = cursor
        page = normalise(_request_json(url, page_params, opener))
        if not page:
            break
        collected.extend(page)
        oldest = min(_ms(c) for c in page)
        if start is not None and oldest <= start:
            break
        if len(page) < page_size:
            break
        next_cursor = oldest - 1 if cursor_name == "end" else oldest
        if cursor is not None and next_cursor >= cursor:
            break
        cursor = next_cursor
    result = _filter(collected, start, end)
    _validate_candidate(result, requested, source)
    return result[-requested:]

def _load_bybit_candles(symbol: str, interval: str, limit: int, start_time: Optional[int], end_time: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    return _fetch_back(_BYBIT_SPOT_URL, {"category":"spot", "symbol":_bybit_symbol(symbol), "interval":_bybit_interval(interval)}, _normalise_bybit, 1000, limit, start_time, end_time, opener, "Bybit spot", "end", end_time)

def _load_okx_candles(symbol: str, interval: str, limit: int, start_time: Optional[int], end_time: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    initial = end_time + 1 if end_time is not None else None
    return _fetch_back(_OKX_CANDLES_URL, {"instId":_okx_symbol(symbol), "bar":_okx_interval(interval)}, _normalise_okx, 300, limit, start_time, end_time, opener, "OKX", "after", initial)

def _load_coinbase_candles(limit: int, end_time: Optional[int], opener: Callable[..., Any], start_time: Optional[int] = None) -> List[Candle]:
    granularity = 300
    cursor = end_time if end_time is not None else int(time.time() * 1000)
    collected: List[Candle] = []
    while len(_dedupe_sort(collected)) < limit:
        params = {"granularity":granularity, "start":_iso(cursor - 300 * granularity * 1000), "end":_iso(cursor)}
        page = _normalise_coinbase(_request_json(_COINBASE_URL, params, opener))
        if not page:
            break
        collected.extend(page)
        oldest = min(_ms(c) for c in page)
        if start_time is not None and oldest <= start_time or len(page) < 300:
            break
        cursor = oldest - granularity * 1000
    result = _filter(collected, start_time, end_time)
    _validate_candidate(result, limit, "Coinbase Exchange")
    return result[-limit:]

def _load_kraken_candles(limit: int, end_time: Optional[int], opener: Callable[..., Any], start_time: Optional[int] = None, symbol: str = "SOLUSDT", interval: str = "5m") -> List[Candle]:
    step = _interval_seconds(interval)
    end = end_time if end_time is not None else int(time.time() * 1000)
    start = start_time if start_time is not None else end - limit * step * 1000
    cursor = max(0, start // 1000)
    collected: List[Candle] = []
    while len(_dedupe_sort(collected)) < limit:
        page = _normalise_kraken(_request_json(_KRAKEN_URL, {"pair":_kraken_symbol(symbol), "interval":max(1, step // 60), "since":cursor}, opener))
        page = [c for c in page if start <= _ms(c) <= end]
        if not page:
            break
        collected.extend(page)
        last = max(_ms(c) for c in page)
        if last >= end or len(page) < 720:
            break
        next_cursor = last // 1000 + step
        if next_cursor <= cursor:
            break
        cursor = next_cursor
    result = _dedupe_sort(collected)
    _validate_candidate(result, limit, "Kraken")
    return result[-limit:]

def _crypto_compare_params(symbol: str, interval: str, limit: int, end_time: Optional[int]) -> dict:
    if _compact(symbol) not in {"SOLUSD", "SOLUSDT"}:
        raise ValueError(f"CryptoCompare fallback only supports SOL/USD, not {symbol}")
    if interval not in {"5m", "5"}:
        raise ValueError(f"CryptoCompare fallback only supports 5m, not {interval}")
    params = {"fsym":"SOL", "tsym":"USD", "aggregate":5, "limit":min(limit, 2000)}
    if end_time is not None:
        params["toTs"] = max(0, int(end_time // 1000))
    return params

def _load_binance_source(url: str, params: dict, limit: int, start: Optional[int], end: Optional[int], opener: Callable[..., Any], source: str) -> List[Candle]:
    return _fetch_back(url, params, _normalise_binance, 1000, limit, start, end, opener, source, "end", end)

def load_binance_candles(symbol: str, interval: str, *, start_time: Optional[int] = None, end_time: Optional[int] = None, limit: int = 1000, opener: Callable[..., Any] = urllib.request.urlopen) -> List[Candle]:
    """Load ascending, validated public candles without API keys."""
    if limit < 1:
        raise ValueError("limit must be positive")
    errors = []
    sources = (
        ("Bybit spot", lambda: _load_bybit_candles(symbol, interval, limit, start_time, end_time, opener)),
        ("OKX", lambda: _load_okx_candles(symbol, interval, limit, start_time, end_time, opener)),
        ("Binance spot", lambda: _load_binance_source(_BINANCE_SPOT_URL, {"symbol":_compact(symbol), "interval":interval}, limit, start_time, end_time, opener, "Binance spot")),
        ("Binance USD-M futures", lambda: _load_binance_source(_BINANCE_FUTURES_URL, {"symbol":_compact(symbol), "interval":interval}, limit, start_time, end_time, opener, "Binance USD-M futures")),
        ("CryptoCompare SOL/USD", lambda: _filter(_normalise_cryptocompare(_request_json(_CRYPTOCOMPARE_URL, _crypto_compare_params(symbol, interval, limit, end_time), opener)), start_time, end_time)[-limit:]),
        ("Coinbase Exchange", lambda: _load_coinbase_candles(limit, end_time, opener, start_time)),
        ("Kraken", lambda: _load_kraken_candles(limit, end_time, opener, start_time, symbol, interval)),
    )
    for source, loader in sources:
        try:
            candles = _dedupe_sort(loader())
            _validate_candidate(candles, limit, source)
        except Exception as exc:
            error = f"{source}: {exc}"
            errors.append(error)
            LOGGER.warning("data source failed: %s", error)
            continue
        LOGGER.info("data source succeeded: %s (%d candles)", source, len(candles))
        return candles[-limit:]
    raise RuntimeError("all public data sources failed: " + "; ".join(errors))

def load_oanda_candles(*, instrument: str, granularity: str, token: Optional[str] = None, practice: bool = True, **_: Any) -> List[Candle]:
    """OANDA remains a deliberate practice-only stub; no token is invented."""
    if not practice:
        raise NotImplementedError("live OANDA loading is unsupported")
    if not token:
        raise RuntimeError("OANDA practice API token required; Mel must create one")
    raise NotImplementedError("OANDA practice candle adapter remains a stub")

def load_local_csv(path: str) -> List[Candle]:
    """CSV fallback; requires timestamp/time/date and OHLC headers."""
    with open(path, "r", newline="", encoding="utf-8") as handle:
        candles = []
        for row in csv.DictReader(handle):
            timestamp = row.get("timestamp") or row.get("time") or row.get("date")
            if timestamp is None:
                raise ValueError("CSV needs timestamp, time, or date")
            candles.append(Candle(timestamp, float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), float(row["volume"]) if row.get("volume") not in (None, "") else None))
    return candles

local_csv_fallback = load_local_csv
