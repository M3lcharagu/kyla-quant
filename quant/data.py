"""Dependency-free data boundaries: Binance public klines, OANDA stub, CSV."""

import csv
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional


LOGGER = logging.getLogger(__name__)
_BINANCE_SPOT_URL = "https://api.binance.com/api/v3/klines"
_BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"
_CRYPTOCOMPARE_URL = "https://min-api.cryptocompare.com/data/v2/histominute"
_COINBASE_URL = "https://api.exchange.coinbase.com/products/SOL-USD/candles?granularity=300"
_KRAKEN_URL = "https://api.kraken.com/0/public/OHLC?pair=SOLUSD&interval=5"
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
    value = float(timestamp)
    if milliseconds:
        value /= 1000.0
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _request_json(
    url: str,
    params: dict,
    opener: Callable[..., Any],
) -> Any:
    query = urllib.parse.urlencode(params)
    request_url = url
    if query:
        request_url += ("&" if "?" in request_url else "?") + query
    request = urllib.request.Request(
        request_url,
        headers={"User-Agent": "kyla-quant/0.1"},
    )
    try:
        with opener(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace").strip()
        except Exception:
            detail = ""
        suffix = f": {detail[:240]}" if detail else ""
        raise RuntimeError(f"HTTP {exc.code} from {url}{suffix}") from exc


def _normalise_binance(payload: Any) -> List[Candle]:
    if isinstance(payload, dict):
        raise RuntimeError(
            f"Binance returned an error: code={payload.get('code')!r}, "
            f"message={payload.get('msg') or payload.get('message') or payload}"
        )
    if not isinstance(payload, list):
        raise RuntimeError(f"Binance returned unexpected JSON: {type(payload).__name__}")

    candles: List[Candle] = []
    for row in payload:
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            raise ValueError("Binance returned a malformed kline row")
        candles.append(
            Candle(
                _utc_datetime(row[0], milliseconds=True),
                float(row[1]),
                float(row[2]),
                float(row[3]),
                float(row[4]),
                float(row[5]),
            )
        )
    return candles


def _normalise_cryptocompare(payload: Any) -> List[Candle]:
    if not isinstance(payload, dict):
        raise RuntimeError("CryptoCompare returned unexpected JSON")
    if payload.get("Response") != "Success":
        raise RuntimeError(
            f"CryptoCompare returned an error: "
            f"{payload.get('Message') or payload.get('Response') or payload}"
        )
    rows = ((payload.get("Data") or {}).get("Data"))
    if not isinstance(rows, list):
        raise RuntimeError("CryptoCompare response did not contain Data.Data")

    candles: List[Candle] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("CryptoCompare returned a malformed candle row")
        volume = row.get("volumefrom") or row.get("volumeto")
        candles.append(
            Candle(
                _utc_datetime(row["time"], milliseconds=False),
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                float(volume),
            )
        )
    return candles


def _normalise_coinbase(payload: Any) -> List[Candle]:
    if not isinstance(payload, list):
        raise RuntimeError("Coinbase returned unexpected JSON")

    candles: List[Candle] = []
    for row in reversed(payload):
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            raise ValueError("Coinbase returned a malformed candle row")
        # Coinbase: [time, low, high, open, close, volume].
        candles.append(
            Candle(
                _utc_datetime(row[0], milliseconds=False),
                float(row[3]),
                float(row[2]),
                float(row[1]),
                float(row[4]),
                float(row[5]),
            )
        )
    return candles


def _normalise_kraken(payload: Any) -> List[Candle]:
    if not isinstance(payload, dict):
        raise RuntimeError("Kraken returned unexpected JSON")
    errors = payload.get("error") or []
    if errors:
        raise RuntimeError(f"Kraken returned an error: {errors}")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("Kraken response did not contain result")
    rows = next((value for key, value in result.items() if key != "last"), None)
    if not isinstance(rows, list):
        raise RuntimeError("Kraken response did not contain an OHLC pair")

    candles: List[Candle] = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 8:
            raise ValueError("Kraken returned a malformed OHLC row")
        # Kraken: [time, open, high, low, close, vwap, volume, count].
        candles.append(
            Candle(
                _utc_datetime(row[0], milliseconds=False),
                float(row[1]),
                float(row[2]),
                float(row[3]),
                float(row[4]),
                float(row[6]),
            )
        )
    return candles


def _validate_candidate(candles: List[Candle], requested: int, source: str) -> None:
    # The normal pagination request is 1,000 rows. Permit a smaller final page
    # while still requiring every normal source response to meet that floor.
    minimum = min(_MIN_CANDLES, requested)
    if len(candles) < minimum:
        raise ValueError(
            f"{source} returned {len(candles)} candles; expected at least {minimum}"
        )

    previous = None
    for candle in candles:
        if previous is not None and candle.timestamp <= previous:
            raise ValueError(f"{source} timestamps are not strictly ascending")
        previous = candle.timestamp
        prices = (candle.open, candle.high, candle.low, candle.close)
        if any(price < _SOL_PRICE_MIN or price > _SOL_PRICE_MAX for price in prices):
            raise ValueError(
                f"{source} returned an implausible SOL price "
                f"(expected {_SOL_PRICE_MIN:g}-{_SOL_PRICE_MAX:g})"
            )
        if candle.volume is None or candle.volume <= 0:
            raise ValueError(f"{source} returned a candle with non-positive volume")


def _cryptocompare_params(
    symbol: str,
    interval: str,
    limit: int,
    end_time: Optional[int],
) -> dict:
    compact = symbol.upper().replace("/", "")
    if compact == "SOLUSDT":
        fsym, tsym = "SOL", "USD"
    elif compact == "SOLUSD":
        fsym, tsym = "SOL", "USD"
    else:
        raise ValueError(f"CryptoCompare fallback only supports SOLUSDT, not {symbol}")
    if interval not in {"5m", "5"}:
        raise ValueError(f"CryptoCompare fallback only supports 5m, not {interval}")

    params = {"fsym": fsym, "tsym": tsym, "aggregate": 5, "limit": min(limit, 2000)}
    if end_time is not None:
        params["toTs"] = max(0, int(end_time // 1000))
    return params


def _load_coinbase_candles(
    limit: int,
    end_time: Optional[int],
    opener: Callable[..., Any],
) -> List[Candle]:
    target = max(_MIN_CANDLES, limit)
    params = {} if end_time is None else {"end": _utc_datetime(end_time, milliseconds=True).isoformat().replace("+00:00", "Z")}
    collected = {}

    for _ in range(100):
        page = _normalise_coinbase(_request_json(_COINBASE_URL, params, opener))
        if not page:
            break
        for candle in page:
            if end_time is None or candle.timestamp.timestamp() * 1000 <= end_time:
                collected[candle.timestamp] = candle
        if len(collected) >= target or len(page) < 300:
            break
        earliest = min(candle.timestamp for candle in page)
        params = {"end": datetime.fromtimestamp(earliest.timestamp() - 300, tz=timezone.utc).isoformat().replace("+00:00", "Z")}

    candles = [collected[key] for key in sorted(collected)]
    _validate_candidate(candles, target, "Coinbase Exchange")
    return candles[-limit:]


def _load_kraken_candles(
    limit: int,
    end_time: Optional[int],
    opener: Callable[..., Any],
) -> List[Candle]:
    candles = _normalise_kraken(_request_json(_KRAKEN_URL, {}, opener))
    if end_time is not None:
        candles = [candle for candle in candles if candle.timestamp.timestamp() * 1000 <= end_time]
    candles = sorted(candles, key=lambda candle: candle.timestamp)
    _validate_candidate(candles, limit, "Kraken")
    return candles[-limit:]


def load_binance_klines(
    symbol: str,
    interval: str,
    *,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    limit: int = 1000,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> List[Candle]:
    """Load validated public candles through ordered, non-geo-blocked fallbacks.

    Binance caps a response at 1,000 rows, so callers may paginate by passing
    ``end_time``. Every adapter emits the same [time, open, high, low, close,
    volume] Candle shape; no credentials or synthetic data are used.
    """
    if not 1 <= limit <= 1000:
        raise ValueError("Binance limit must be between 1 and 1000")

    binance_params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    if start_time is not None:
        binance_params["startTime"] = start_time
    if end_time is not None:
        binance_params["endTime"] = end_time

    sources = (
        ("Binance spot", _BINANCE_SPOT_URL, binance_params, _normalise_binance),
        ("Binance USD-M futures", _BINANCE_FUTURES_URL, binance_params, _normalise_binance),
        (
            "CryptoCompare SOL/USD",
            _CRYPTOCOMPARE_URL,
            _cryptocompare_params(symbol, interval, limit, end_time),
            _normalise_cryptocompare,
        ),
    )
    errors = []
    for source, url, params, normalise in sources:
        try:
            candles = normalise(_request_json(url, params, opener))
            _validate_candidate(candles, limit, source)
        except Exception as exc:
            error = f"{source}: {exc}"
            errors.append(error)
            LOGGER.warning("data source failed: %s", error)
            continue
        LOGGER.info("data source succeeded: %s (%d candles)", source, len(candles))
        return candles

    # Key-free fallbacks deliberately follow the existing three sources.
    fallbacks = (
        ("Coinbase Exchange", lambda: _load_coinbase_candles(limit, end_time, opener)),
        ("Kraken", lambda: _load_kraken_candles(limit, end_time, opener)),
    )
    for source, load in fallbacks:
        try:
            candles = load()
        except Exception as exc:
            error = f"{source}: {exc}"
            errors.append(error)
            LOGGER.warning("data source failed: %s", error)
            continue
        LOGGER.info("data source succeeded: %s (%d candles)", source, len(candles))
        return candles

    raise RuntimeError("all public data sources failed: " + "; ".join(errors))


def load_oanda_candles(
    *,
    instrument: str,
    granularity: str,
    token: Optional[str] = None,
    practice: bool = True,
    **_: Any,
) -> List[Candle]:
    """Stub for practice API.

    Practice endpoint: https://api-fxpractice.oanda.com/v3/instruments/{instrument}/candles
    with Authorization: Bearer <token>. Mel must create a practice API token.
    No token is invented or stored here; live mode is unsupported in v0.1.
    """
    if not practice:
        raise NotImplementedError("live OANDA loading is unsupported in v0.1")
    if not token:
        raise RuntimeError("OANDA practice API token required; Mel must create one")
    raise NotImplementedError("OANDA practice candle adapter remains a stub")


def load_local_csv(path: str) -> List[Candle]:
    """CSV fallback; requires timestamp/time/date and open,high,low,close headers."""
    with open(path, "r", newline="", encoding="utf-8") as handle:
        candles = []
        for row in csv.DictReader(handle):
            timestamp = row.get("timestamp") or row.get("time") or row.get("date")
            if timestamp is None:
                raise ValueError("CSV needs timestamp, time, or date")
            candles.append(
                Candle(
                    timestamp,
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    float(row["volume"]) if row.get("volume") not in (None, "") else None,
                )
            )
    return candles


local_csv_fallback = load_local_csv
