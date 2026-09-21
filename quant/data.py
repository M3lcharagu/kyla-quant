"""Key-free public OHLCV adapters with bounded pagination and validation."""
from __future__ import annotations
import csv, json, logging, ssl, time
import urllib.error, urllib.parse, urllib.request
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

# Preserve the repository's deliberately unverified public-data opener.
_SSL = ssl._create_unverified_context()
urlopen = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_SSL)).open

@dataclass(frozen=True)
class Candle:
    timestamp: Any
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None

def _ms(value: Any) -> int:
    v = float(value)
    return int(v if v > 10_000_000_000 else v * 1000)

def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")

def _request_json(url: str, params: dict[str, Any]) -> Any:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(url + ("&" if "?" in url else "?") + query, headers={"User-Agent": "kyla-quant/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try: detail = exc.read().decode("utf-8", "replace")[:240]
        except Exception: detail = ""
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc

def _candle(row: Any, indexes: tuple[int, int, int, int, int, int], milliseconds: bool = True) -> Candle:
    if not isinstance(row, (list, tuple)) or len(row) <= max(indexes):
        raise ValueError("malformed OHLCV row")
    ti, oi, hi, li, ci, vi = indexes
    return Candle(_iso(_ms(row[ti])) if milliseconds else _iso(int(float(row[ti]) * 1000)), float(row[oi]), float(row[hi]), float(row[li]), float(row[ci]), float(row[vi]) if row[vi] not in (None, "") else None)

def _validate(candles: List[Candle], requested: int, source: str) -> None:
    if not candles: raise ValueError(f"{source} returned no usable candles")
    previous = -1
    for c in candles:
        if _ms(c.timestamp) <= previous: raise ValueError(f"{source} timestamps are not strictly ascending")
        previous = _ms(c.timestamp)
        if any(p <= 0 for p in (c.open, c.high, c.low, c.close)) or (c.volume is not None and c.volume < 0):
            raise ValueError(f"{source} returned invalid OHLCV values")
        if c.high < max(c.open, c.close, c.low) or c.low > min(c.open, c.close, c.high):
            raise ValueError(f"{source} returned inconsistent OHLC")
    if len(candles) < min(requested, 50): LOGGER.warning("%s supplied only %d/%d requested candles", source, len(candles), requested)

def _dedupe(rows: List[Candle]) -> List[Candle]:
    return [dict((_ms(c.timestamp), c) for c in rows)[k] for k in sorted(dict((_ms(c.timestamp), c) for c in rows))]

def _interval_seconds(interval: str) -> int:
    s = interval.lower().strip()
    if s.isdigit(): return int(s) * 60
    if s.endswith("mo"): return int(s[:-2]) * 30 * 86400
    units = {"m": 60, "h": 3600, "d": 86400, "w": 604800}
    for suffix, mult in units.items():
        if s.endswith(suffix): return int(s[:-1]) * mult
    raise ValueError(f"unsupported interval: {interval}")

def _binance_interval(interval: str) -> str: return interval.lower()
def _bybit_interval(interval: str) -> str: return interval.lower().replace("h", "h").replace("d", "d")
def _okx_interval(interval: str) -> str:
    s = interval.lower(); return {"1m":"1m","3m":"3m","5m":"5m","15m":"15m","30m":"30m","1h":"1H","2h":"2H","4h":"4H","6h":"6H","12h":"12H","1d":"1D","1w":"1W"}.get(s, s)

def _compact(symbol: str) -> str: return symbol.upper().replace("/", "").replace("-", "").replace("_", "")
def _quote_symbol(symbol: str, quote: str = "USDT") -> str:
    s = _compact(symbol)
    return s if s.endswith(quote) else s + quote

def _fetch_binance(symbol: str, interval: str, limit: int, start: Optional[int], end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    out: List[Candle] = []; cursor = end
    for _ in range(20):
        if len(out) >= limit: break
        n = min(1000, limit - len(out)); p = {"symbol": _quote_symbol(symbol), "interval": _binance_interval(interval), "limit": n}
        if start is not None: p["startTime"] = start
        if cursor is not None: p["endTime"] = cursor
        payload = _request_json(BINANCE_SPOT_URL, p)
        if not isinstance(payload, list): raise ValueError("Binance response was not a list")
        page = [_candle(x, (0,1,2,3,4,5)) for x in payload]
        if not page: break
        out.extend(page); oldest = min(_ms(x.timestamp) for x in page)
        if start is not None or len(page) < n: break
        cursor = oldest - 1; time.sleep(.05)
    return _dedupe(out)[-limit:]

def _fetch_bybit(symbol: str, interval: str, limit: int, start: Optional[int], end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    out: List[Candle] = []; cursor = end
    for _ in range(20):
        n=min(1000, limit-len(out)); p={"category":"spot","symbol":_quote_symbol(symbol),"interval":_bybit_interval(interval),"limit":n}
        if start is not None: p["start"] = start
        if cursor is not None: p["end"] = cursor
        payload=_request_json(BYBIT_SPOT_URL,p); result=payload.get("result") if isinstance(payload,dict) else None
        rows=result.get("list") if isinstance(result,dict) else None
        if not isinstance(rows,list): raise ValueError("Bybit response missing result.list")
        page=[_candle(x,(0,1,2,3,4,5)) for x in rows]
        out.extend(page)
        if not page or start is not None or len(page)<n: break
        cursor=min(_ms(x.timestamp) for x in page)-1
    return _dedupe(out)[-limit:]

def _fetch_okx(symbol: str, interval: str, limit: int, start: Optional[int], end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    out=[]; after=end+1 if end is not None else None
    for _ in range(20):
        n=min(300,limit-len(out)); p={"instId":_compact(symbol).replace("USDT","-USDT"),"bar":_okx_interval(interval),"limit":n}
        if after is not None: p["after"]=after
        payload=_request_json(OKX_CANDLES_URL,p); rows=payload.get("data") if isinstance(payload,dict) and payload.get("code")=="0" else None
        if not isinstance(rows,list): raise ValueError("OKX response missing data")
        page=[_candle(x,(0,1,2,3,4,5)) for x in rows]; out.extend(page)
        if not page or len(page)<n: break
        after=min(_ms(x.timestamp) for x in page)-1
    return _dedupe(out)[-limit:]

def _fetch_gate(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    payload=_request_json(GATE_SPOT_URL,{"currency_pair":"SOL_USDT","interval":"5m","limit":min(limit,1000)})
    if not isinstance(payload,list): raise ValueError("Gate.io response was not a list")
    return [_candle(x,(0,5,3,4,2,1)) for x in payload]

def _fetch_kucoin(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    payload=_request_json(KUCOIN_URL,{"symbol":"SOL-USDT","type":"5min"})
    rows=payload.get("data") if isinstance(payload,dict) and payload.get("code")=="200000" else None
    if not isinstance(rows,list): raise ValueError("KuCoin response missing data")
    return [_candle(x,(0,1,2,3,4,5),False) for x in rows[-min(limit,1500):]]

def _fetch_mexc(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    payload=_request_json(MEXC_URL,{"symbol":"SOLUSDT","interval":"5m","limit":min(limit,1000)})
    if not isinstance(payload,list): raise ValueError("MEXC response was not a list")
    return [_candle(x,(0,1,2,3,4,5)) for x in payload]

def _fetch_bitfinex(limit: int, end: Optional[int], opener: Callable[..., Any]) -> List[Candle]:
    out=[]; cursor=end
    for _ in range(20):
        n=min(1000,limit-len(out)); url=f"{BITFINEX_URL}/trade:5m:tSOLUSD/hist"; p={"limit":n,"sort":1}
        if cursor is not None: p["end"]=cursor
        payload=_request_json(url,p)
        if not isinstance(payload,list): raise ValueError("Bitfinex response was not a list")
        page=[_candle(x,(0,2,3,4,1,5)) for x in payload]; out.extend(page)
        if not page or len(page)<n: break
        cursor=min(_ms(x.timestamp) for x in page)-1
    return _dedupe(out)[-limit:]

def _fetch_bitstamp(limit: int, opener: Callable[..., Any]) -> List[Candle]:
    payload=_request_json(f"{BITSTAMP_URL}/solusd/",{"step":300,"limit":min(limit,1000)})
    rows=payload.get("data",{}).get("ohlc") if isinstance(payload,dict) else None
    if not isinstance(rows,list): raise ValueError("Bitstamp response missing data.ohlc")
    return [_candle(x,("timestamp" if False else 0,1,2,3,4,5)) for x in []] if False else [Candle(_iso(int(float(x["timestamp"])*1000)),float(x["open"]),float(x["high"]),float(x["low"]),float(x["close"]),float(x.get("volume",0))) for x in rows]

def load_binance_candles(symbol: str, interval: str, *, start_time: Optional[int]=None, end_time: Optional[int]=None, limit: int=1000, opener: Callable[..., Any]=urlopen) -> List[Candle]:
    """Load ascending, validated, key-free public candles; exchange fallbacks are bounded."""
    if limit < 1: raise ValueError("limit must be positive")
    errors=[]
    sources=[("Binance spot",lambda:_fetch_binance(symbol,interval,limit,start_time,end_time,opener)),("Bybit spot",lambda:_fetch_bybit(symbol,interval,limit,start_time,end_time,opener)),("OKX",lambda:_fetch_okx(symbol,interval,limit,start_time,end_time,opener))]
    if _compact(symbol)=="SOLUSDT" and interval.lower() in ("5m","5"): sources += [("Gate.io spot",lambda:_fetch_gate(limit,opener)),("KuCoin",lambda:_fetch_kucoin(limit,opener)),("MEXC",lambda:_fetch_mexc(limit,opener)),("Bitfinex",lambda:_fetch_bitfinex(limit,end_time,opener)),("Bitstamp",lambda:_fetch_bitstamp(limit,opener))]
    for name, loader in sources:
        try:
            rows=_dedupe(loader()); _validate(rows,limit,name); LOGGER.info("data source succeeded: %s (%d candles)",name,len(rows)); return rows[-limit:]
        except Exception as exc:
            errors.append(f"{name}: {exc}"); LOGGER.warning("data source failed: %s",errors[-1])
    raise RuntimeError("all public data sources failed: " + "; ".join(errors))

load_binance_klines = load_binance_candles

def load_local_csv(path: str) -> List[Candle]:
    with open(path,"r",newline="",encoding="utf-8") as handle:
        out=[]
        for row in csv.DictReader(handle):
            ts=row.get("timestamp") or row.get("time") or row.get("date")
            out.append(Candle(ts,float(row["open"]),float(row["high"]),float(row["low"]),float(row["close"]),float(row["volume"]) if row.get("volume") else None))
    _validate(out,len(out),"CSV"); return _dedupe(out)

def load_oanda_candles(*, instrument: str, granularity: str, token: Optional[str]=None, practice: bool=True, **_: Any) -> List[Candle]:
    raise NotImplementedError("live OANDA loading requires an explicitly supplied token")

local_csv_fallback = load_local_csv
