"""Key-free public OHLCV adapters with bounded pagination and validation."""
from __future__ import annotations
import csv, io, json, logging, ssl, time, urllib.error, urllib.parse, urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional
LOGGER=logging.getLogger(__name__)
BINANCE_SPOT_URL="https://api.binance.com/api/v3/klines"
BYBIT_SPOT_URL="https://api.bybit.com/v5/market/kline"
OKX_CANDLES_URL="https://www.okx.com/api/v5/market/candles"
GATE_SPOT_URL="https://api.gateio.ws/api/v4/spot/candlesticks"
KUCOIN_URL="https://api.kucoin.com/api/v1/market/candles"
MEXC_URL="https://api.mexc.com/api/v3/klines"
BITFINEX_URL="https://api-pub.bitfinex.com/v2/candles"
BITSTAMP_URL="https://www.bitstamp.net/api/v2/ohlc"
KRAKEN_OHLC_URL="https://api.kraken.com/0/public/OHLC"
COINBASE_CANDLES_URL="https://api.exchange.coinbase.com/products/SOL-USD/candles"
YAHOO_CHART_URL="https://query1.finance.yahoo.com/v8/finance/chart/"
STOOQ_CSV_URL="https://stooq.com/q/d/l/"
_SSL=ssl._create_unverified_context()
_BROWSER_USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
urlopen=urllib.request.build_opener(urllib.request.HTTPSHandler(context=_SSL)).open
@dataclass(frozen=True)
class Candle:
    timestamp:Any; open:float; high:float; low:float; close:float; volume:Optional[float]=None

def _normalize_timestamp(value:Any,time_value:Any=None)->str:
    if time_value not in (None,""): value=f"{str(value).strip()}T{str(time_value).strip()}"
    if isinstance(value,bool) or value is None: raise ValueError(f"invalid timestamp: {value!r}")
    if isinstance(value,(int,float)):
        n=float(value)
        if n!=n or n in (float("inf"),float("-inf")): raise ValueError(f"invalid timestamp: {value!r}")
        dt=datetime.fromtimestamp(n/1000 if n>1_000_000_000_000 else n,tz=timezone.utc)
    else:
        text=str(value).strip()
        if not text: raise ValueError("empty timestamp")
        dt=datetime.fromisoformat(text[:-1]+"+00:00" if text.endswith("Z") else text)
        dt=(dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc))
    return dt.isoformat().replace("+00:00","Z")

def _ms(value:Any)->int:
    dt=datetime.fromisoformat(_normalize_timestamp(value)[:-1]+"+00:00")
    return int(dt.timestamp()*1000)

def _iso(ms:int)->str: return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat().replace("+00:00","Z")
def _compact(s:str)->str: return s.upper().replace("/","").replace("-","").replace("_","")
def _quote(s:str)->str: return _compact(s) if _compact(s).endswith("USDT") else _compact(s)+"USDT"
def _request_bytes(url:str,params:dict[str,Any])->bytes:
    q=urllib.parse.urlencode(params); req=urllib.request.Request(url+("?"+q if q else ""),headers={"User-Agent":_BROWSER_USER_AGENT,"Accept":"*/*"})
    try:
        with urlopen(req,timeout=30) as r:return r.read()
    except urllib.error.HTTPError as e:
        try: detail=e.read().decode("utf-8","replace")[:200]
        except Exception: detail=""
        raise RuntimeError(f"HTTP {e.code} from {url}: {detail}") from e
def _request_json(url:str,params:dict[str,Any])->Any:return json.loads(_request_bytes(url,params).decode("utf-8"))
def _dedupe(rows:List[Candle])->List[Candle]:
    d={_ms(c.timestamp):c for c in rows}; return [d[k] for k in sorted(d)]
def _validate(rows:List[Candle],requested:int,source:str)->None:
    if not rows: raise ValueError(f"{source} returned no usable candles")
    prev=-1
    for c in rows:
        t=_ms(c.timestamp)
        if t<=prev: raise ValueError(f"{source} timestamps are not strictly ascending")
        prev=t
        if any(v<=0 for v in (c.open,c.high,c.low,c.close)): raise ValueError(f"{source} returned invalid OHLC values")
        if c.high<max(c.open,c.close,c.low) or c.low>min(c.open,c.close,c.high): raise ValueError(f"{source} returned inconsistent OHLC")
        if c.volume is not None and c.volume<0: raise ValueError(f"{source} returned negative volume")
    if len(rows)<min(requested,50): LOGGER.warning("%s supplied only %d/%d requested candles",source,len(rows),requested)
def _row(row:Any,idx:tuple[int,int,int,int,int],seconds:bool=False)->Candle:
    ti,oi,hi,li,ci=idx; ts=_normalize_timestamp(float(row[ti])*1000 if seconds else row[ti]); v=row[5] if len(row)>5 else None
    return Candle(ts,float(row[oi]),float(row[hi]),float(row[li]),float(row[ci]),None if v in (None,"") else float(v))
def _parsed(source:str,rows:Any,idx:tuple[int,int,int,int,int],limit:int,reverse:bool=False,seconds:bool=False)->List[Candle]:
    out=[]; skipped=0
    for r in (reversed(rows) if reverse else rows):
        try: out.append(_row(r,idx,seconds))
        except (TypeError,ValueError,IndexError,KeyError): skipped+=1
    LOGGER.info("data source parse: source=%s candles=%d skipped=%d",source,len(out),skipped)
    return _dedupe(out)[-limit:],skipped

def _fetch_binance(symbol:str,interval:str,limit:int,start:Optional[int],end:Optional[int],opener:Callable[...,Any])->List[Candle]:
    out=[]; cursor=start; skipped=0
    for _ in range(20):
        n=min(1000,limit-len(out));
        if n<=0: break
        p={"symbol":_quote(symbol),"interval":interval,"limit":n};
        if cursor is not None:p["startTime"]=cursor
        if end is not None:p["endTime"]=end
        data=_request_json(BINANCE_SPOT_URL,p)
        if not isinstance(data,list): raise ValueError("Binance response was not a list")
        page,s=_parsed("Binance spot",data,(0,1,2,3,4),n); skipped+=s; out+=page
        if len(page)<n: break
        oldest=min(_ms(c.timestamp) for c in page); cursor=oldest-1
        if start is not None and oldest<=start: break
        time.sleep(.05)
    LOGGER.info("data source pagination: source=Binance spot skipped=%d",skipped); return _dedupe(out)[-limit:]
def _fetch_bybit(symbol:str,interval:str,limit:int,start:Optional[int],end:Optional[int],opener:Callable[...,Any])->List[Candle]:
    out=[]; cursor=end; skipped=0
    for _ in range(20):
        n=min(1000,limit-len(out));
        if n<=0: break
        p={"category":"spot","symbol":_quote(symbol),"interval":interval.lower().replace("h","H").replace("d","D"),"limit":n}
        if start is not None:p["start"]=start
        if cursor is not None:p["end"]=cursor
        payload=_request_json(BYBIT_SPOT_URL,p); result=payload.get("result",{}) if isinstance(payload,dict) else {}; rows=result.get("list")
        if not isinstance(rows,list): raise ValueError("Bybit response missing result.list")
        page,s=_parsed("Bybit spot",rows,(0,1,2,3,4),n,True); skipped+=s; out+=page
        if len(page)<n: break
        oldest=min(_ms(c.timestamp) for c in page); cursor=oldest-1
        if start is not None and oldest<=start: break
    LOGGER.info("data source pagination: source=Bybit spot skipped=%d",skipped); return _dedupe(out)[-limit:]
def _fetch_okx(symbol:str,interval:str,limit:int,start:Optional[int],end:Optional[int],opener:Callable[...,Any])->List[Candle]:
    p={"instId":_compact(symbol).replace("USDT","-USDT"),"bar":interval.lower().replace("h","H").replace("d","D"),"limit":min(limit,300)}
    data=_request_json(OKX_CANDLES_URL,p); rows=data.get("data") if isinstance(data,dict) and data.get("code")=="0" else None
    if not isinstance(rows,list): raise ValueError("OKX response missing data")
    parsed,_=_parsed("OKX",rows,(0,1,2,3,4),limit,True); return parsed
def _fetch_simple(url:str,params:dict[str,Any],source:str,idx:tuple[int,int,int,int,int],limit:int,opener:Callable[...,Any],rows_key:Optional[str]=None,seconds:bool=False)->List[Candle]:
    data=_request_json(url,params); rows=data.get(rows_key) if rows_key and isinstance(data,dict) else data
    if not isinstance(rows,list): raise ValueError(f"{source} response missing rows")
    parsed,_=_parsed(source,rows,idx,limit,False,seconds); return parsed

def _fetch_kraken(symbol:str,limit:int,opener:Callable[...,Any])->List[Candle]:
    out=[]; since=None; seen=set(); skipped=0
    for _ in range(20):
        if len(out)>=min(limit,20000): break
        p={"pair":"SOLUSD","interval":5};
        if since is not None:p["since"]=since
        payload=_request_json(KRAKEN_OHLC_URL,p)
        if not isinstance(payload,dict) or payload.get("error"): raise ValueError(f"Kraken response error: {payload.get('error') if isinstance(payload,dict) else payload}")
        result=payload.get("result",{}); rows=next((v for k,v in result.items() if k!="last" and isinstance(v,list)),None) if isinstance(result,dict) else None
        if not isinstance(rows,list): raise ValueError("Kraken response missing OHLC rows")
        page,s=_parsed("Kraken OHLC",rows,(0,1,2,3,4),20000); skipped+=s
        if not page: break
        out+=page; oldest=min(_ms(c.timestamp)//1000 for c in page)
        if oldest in seen or (since is not None and oldest>=since): break
        seen.add(oldest); since=oldest
        if len(rows)<720: break
    LOGGER.info("data source pagination: source=Kraken OHLC candles=%d skipped=%d",len(out),skipped); return _dedupe(out)[-min(limit,20000):]
def _fetch_coinbase(limit:int,opener:Callable[...,Any])->List[Candle]:
    out=[]; end=int(time.time()*1000); skipped=0; window=300*300*1000
    for _ in range(67):
        if len(out)>=min(limit,20000): break
        data=_request_json(COINBASE_CANDLES_URL,{"granularity":300,"start":_iso(end-window),"end":_iso(end)})
        if not isinstance(data,list): raise ValueError("Coinbase candles response was not a list")
        page,s=_parsed("Coinbase candles",data,(0,3,2,1,4),300); skipped+=s
        if not page: break
        out+=page; oldest=min(_ms(c.timestamp) for c in page)
        if oldest>=end: break
        end=oldest-1
        if len(page)<300: break
    LOGGER.info("data source pagination: source=Coinbase candles=%d skipped=%d",len(out),skipped); return _dedupe(out)[-min(limit,20000):]
def _fetch_yahoo(symbol:str,limit:int,opener:Callable[...,Any])->List[Candle]:
    url=YAHOO_CHART_URL+urllib.parse.quote(f"{_compact(symbol).upper()}-USD",safe=""); payload=_request_json(url,{"interval":"5m","range":"1mo"})
    result=payload.get("chart",{}).get("result") if isinstance(payload,dict) else None; chart=result[0] if isinstance(result,list) and result else None
    ts=chart.get("timestamp") if isinstance(chart,dict) else None; q=chart.get("indicators",{}).get("quote",[{}])[0] if isinstance(chart,dict) else {}
    if not isinstance(ts,list) or not isinstance(q,dict): raise ValueError("Yahoo response missing chart arrays")
    out=[]; skipped=0
    for i,t in enumerate(ts):
        try:
            vals=[q[f][i] for f in ("open","high","low","close","volume")]
            if any(v is None for v in vals[:4]): skipped+=1; continue
            out.append(Candle(_normalize_timestamp(t),float(vals[0]),float(vals[1]),float(vals[2]),float(vals[3]),None if vals[4] is None else float(vals[4])))
        except (TypeError,ValueError,IndexError,KeyError): skipped+=1
    LOGGER.info("data source parse: source=Yahoo Finance chart candles=%d skipped=%d",len(out),skipped); return _dedupe(out)[-limit:]
def _fetch_stooq(symbol:str,limit:int,opener:Callable[...,Any])->List[Candle]:
    text=_request_bytes(STOOQ_CSV_URL,{"s":f"{_compact(symbol).lower()}usd","i":"300"}).decode("utf-8","replace"); out=[]; skipped=0
    for r in csv.DictReader(io.StringIO(text)):
        try:
            stamp=_normalize_timestamp(r.get("Date") or r.get("date"),r.get("Time") or r.get("time")); vals=[r[k] for k in ("Open","High","Low","Close")]; v=r.get("Volume") or r.get("volume")
            out.append(Candle(stamp,*[float(x) for x in vals],None if v in (None,"") else float(v)))
        except (TypeError,ValueError,KeyError): skipped+=1
    LOGGER.info("data source parse: source=Stooq CSV candles=%d skipped=%d",len(out),skipped); return _dedupe(out)[-limit:]
def load_binance_candles(symbol:str,interval:str,*,start_time:Optional[int]=None,end_time:Optional[int]=None,limit:int=1000,opener:Callable[...,Any]=urlopen)->List[Candle]:
    if limit<1: raise ValueError("limit must be positive")
    sources=[("Binance spot",lambda:_fetch_binance(symbol,interval,limit,start_time,end_time,opener)),("Bybit spot",lambda:_fetch_bybit(symbol,interval,limit,start_time,end_time,opener)),("OKX",lambda:_fetch_okx(symbol,interval,limit,start_time,end_time,opener))]
    if _compact(symbol) in ("SOLUSDT","SOLUSD") and interval.lower() in ("5m","5"):
        sources += [("Gate.io spot",lambda:_fetch_simple(GATE_SPOT_URL,{"currency_pair":"SOL_USDT","interval":"5m","limit":min(limit,1000)},"Gate.io spot",(0,5,3,4,2),limit,opener,seconds=True)),("KuCoin",lambda:_fetch_simple(KUCOIN_URL,{"symbol":"SOL-USDT","type":"5min"},"KuCoin",(0,1,2,3,4),limit,opener,"data",True)),("MEXC",lambda:_fetch_simple(MEXC_URL,{"symbol":"SOLUSDT","interval":"5m","limit":min(limit,1000)},"MEXC",(0,1,2,3,4),limit,opener)),("Bitfinex",lambda:_fetch_simple(f"{BITFINEX_URL}/trade:5m:tSOLUSD/hist",{"limit":min(limit,1000),"sort":1},"Bitfinex",(0,1,2,3,4),limit,opener)),("Bitstamp",lambda:_fetch_simple(f"{BITSTAMP_URL}/solusd/",{"step":300,"limit":min(limit,1000)},"Bitstamp",("timestamp","open","high","low","close"),limit,opener,"data")),("Kraken OHLC",lambda:_fetch_kraken(symbol,limit,opener)),("Coinbase candles",lambda:_fetch_coinbase(limit,opener))]
    sources += [("Yahoo Finance chart",lambda:_fetch_yahoo(symbol,limit,opener)),("Stooq CSV",lambda:_fetch_stooq(symbol,limit,opener))]
    errors=[]
    for name,loader in sources:
        try:
            rows=_dedupe(loader()); _validate(rows,limit,name)
            LOGGER.info("data source result: source=%s status=SUCCESS candles=%d first=%s last=%s skipped=see-parse-log",name,len(rows),rows[0].timestamp,rows[-1].timestamp); return rows[-limit:]
        except Exception as exc:
            errors.append(f"{name}: {exc}"); LOGGER.warning("data source result: source=%s status=FAILURE candles=0 first=- last=- skipped=see-parse-log failure=%s",name,exc)
    raise RuntimeError("all public data sources failed: "+"; ".join(errors))
load_binance_klines=load_binance_candles
def load_local_csv(path:str)->List[Candle]:
    out=[]; skipped=0
    with open(path,"r",newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                out.append(Candle(_normalize_timestamp(r.get("timestamp") or r.get("time") or r.get("date")),float(r["open"]),float(r["high"]),float(r["low"]),float(r["close"]),None if r.get("volume") in (None,"") else float(r["volume"])))
            except (TypeError,ValueError,KeyError): skipped+=1
    rows=_dedupe(out); _validate(rows,len(rows),"CSV"); LOGGER.info("data source result: source=CSV status=SUCCESS candles=%d first=%s last=%s skipped=%d",len(rows),rows[0].timestamp,rows[-1].timestamp,skipped); return rows
def load_oanda_candles(*,instrument:str,granularity:str,token:Optional[str]=None,practice:bool=True,**_:Any)->List[Candle]: raise NotImplementedError("live OANDA loading requires an explicitly supplied token")
local_csv_fallback=load_local_csv
