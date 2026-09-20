#!/usr/bin/env python3
"""Network-free SQLite trading journal CLI (Python 3.9+, standard library only)."""
from __future__ import annotations
import argparse, csv, io, json, re, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "journal" / "trades.db"
COLS = ("account_id","symbol","asset_class","direction","status","entry_time","exit_time","size","entry_price","exit_price","stop_loss","profit_target","fees","gross_pnl","net_pnl","currency","screenshot_path","tags","mistakes","playbook","notes","rating","reviewed")
ALL = ("id",) + COLS
SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
 id INTEGER PRIMARY KEY AUTOINCREMENT, account_id TEXT, symbol TEXT NOT NULL,
 asset_class TEXT, direction TEXT NOT NULL CHECK(direction IN ('long','short')),
 status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','win','loss','breakeven')),
 entry_time TEXT, exit_time TEXT, size REAL, entry_price REAL, exit_price REAL,
 stop_loss REAL, profit_target REAL, fees REAL NOT NULL DEFAULT 0, gross_pnl REAL,
 net_pnl REAL, currency TEXT, screenshot_path TEXT, tags TEXT, mistakes TEXT,
 playbook TEXT, notes TEXT, rating INTEGER, reviewed INTEGER NOT NULL DEFAULT 0
 CHECK(reviewed IN (0,1))
)
"""
# KYLA Edge Score is an original 0-100 composite, not LuxAlgo's: 35% trade-win
# rate + 25% PF/(PF+1) scaled to 100 + 20% day-win rate + 10% reviewed-trade
# rate + 10% expectancy quality (100 positive, 50 zero, 0 negative).
ALIASES = {
 "account_id":"account account id accountid portfolio", "symbol":"ticker asset instrument market",
 "asset_class":"asset class assetclass market type asset type", "direction":"side trade direction position buy sell",
 "status":"result outcome trade result", "entry_time":"open time date opened opened at entry timestamp entry date date in time in",
 "exit_time":"close time date closed closed at exit timestamp exit date date out time out",
 "size":"quantity qty contracts volume position size amount", "entry_price":"entry entry rate open price price in average entry",
 "exit_price":"exit close price price out average exit", "stop_loss":"stop loss stop sl stoploss",
 "profit_target":"take profit target tp profit target takeprofit", "fees":"fee commission commissions cost costs trading fees",
 "gross_pnl":"gross pnl gross p&l gross profit pnl before fees profit before fees",
 "net_pnl":"net pnl net p&l net profit profit loss p&l pnl realized pnl realized profit profit",
 "currency":"quote currency ccy", "screenshot_path":"screenshot screenshot file image chart chart image",
 "tags":"tag labels label", "mistakes":"mistake errors error rule breaks rule break",
 "playbook":"setup strategy system playbook name", "notes":"comment comments journal description",
 "rating":"score review score", "reviewed":"review complete is reviewed reviewed?"
}
def key(v): return re.sub(r"[^a-z0-9]+", " ", str(v).lower()).strip()
def text(v):
 if v is None: return None
 if isinstance(v, (list,tuple)): return ", ".join(map(str,v)) or None
 if isinstance(v, dict): return json.dumps(v, ensure_ascii=False, sort_keys=True)
 v = str(v).strip(); return v or None
def num(v):
 if v is None or isinstance(v,bool): return None
 if isinstance(v,(int,float)): return float(v)
 s = str(v).strip()
 if not s or s.lower() in {"na","n/a","null","none","-","—"}: return None
 neg = s.startswith("(") and s.endswith(")")
 s = s.strip("() ").replace(",","")
 s = re.sub(r"^[^0-9+\\-.]+", "", s); s = re.sub(r"[^0-9eE+\\-.]+$", "", s)
 try: n = float(s)
 except ValueError: return None
 return -n if neg else n
def integer(v):
 n=num(v); return None if n is None else int(n)
def boolean(v):
 if isinstance(v,bool): return int(v)
 if v is None: return 0
 if isinstance(v,(int,float)): return int(bool(v))
 return int(str(v).strip().lower() in {"1","true","yes","y","on","done"})
def val(src, field):
 for candidate in (field,) + tuple(ALIASES.get(field," ").split()):
  # aliases containing spaces must be considered as phrases, not split words
  candidate = key(candidate)
  if candidate in src and src[candidate] not in (None,""): return src[candidate]
 return None
def direction(v):
 v=text(v); v=v.lower() if v else None
 return {"buy":"long","b":"long","bull":"long","bullish":"long","sell":"short","s":"short","bear":"short","bearish":"short"}.get(v,v if v in {"long","short"} else None)
def status(v):
 v=text(v); v=v.lower() if v else None
 return {"active":"open","pending":"open","in progress":"open","won":"win","winner":"win","profit":"win","profitable":"win","lost":"loss","loser":"loss","break even":"breakeven","flat":"breakeven","be":"breakeven","0":"breakeven"}.get(v,v if v in {"open","win","loss","breakeven"} else None)
def normalize(row):
 if not isinstance(row,dict): raise ValueError("row is not an object")
 src={key(k):v for k,v in row.items()}; out={}
 out["id"]=integer(val(src,"id")); out["account_id"]=text(val(src,"account_id")); out["symbol"]=text(val(src,"symbol")); out["asset_class"]=text(val(src,"asset_class")); out["direction"]=direction(val(src,"direction")); out["status"]=status(val(src,"status"))
 for f in ("entry_time","exit_time","currency","screenshot_path","tags","mistakes","playbook","notes"): out[f]=text(val(src,f))
 for f in ("size","entry_price","exit_price","stop_loss","profit_target","fees","gross_pnl","net_pnl"): out[f]=num(val(src,f))
 out["fees"] = out["fees"] or 0.0; out["rating"]=integer(val(src,"rating")); out["reviewed"]=boolean(val(src,"reviewed"))
 if not out["symbol"]: raise ValueError("symbol is required")
 if not out["direction"]: raise ValueError("direction must be long or short (buy/sell accepted)")
 if out["gross_pnl"] is None and out["entry_price"] is not None and out["exit_price"] is not None and out["size"] is not None:
  sign=1 if out["direction"]=="long" else -1; out["gross_pnl"]=(out["exit_price"]-out["entry_price"])*out["size"]*sign
 if out["net_pnl"] is None and out["gross_pnl"] is not None: out["net_pnl"]=out["gross_pnl"]-out["fees"]
 if out["gross_pnl"] is None and out["net_pnl"] is not None: out["gross_pnl"]=out["net_pnl"]+out["fees"]
 if out["status"] is None:
  p=out["net_pnl"]; out["status"]="open" if p is None else ("win" if p>0 else "loss" if p<0 else "breakeven")
 return out
def connect(path):
 path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(str(path)); c.row_factory=sqlite3.Row; c.execute(SCHEMA); c.commit(); return c
def insert(c, t, keep_id=False):
 fields=list(COLS); values=[t.get(f) for f in fields]; ident=t.get("id")
 if keep_id and ident and c.execute("SELECT 1 FROM trades WHERE id=?",(ident,)).fetchone() is None: fields.insert(0,"id"); values.insert(0,ident)
 cur=c.execute("INSERT INTO trades ({}) VALUES ({})".format(",".join(fields),",".join("?"*len(fields))),values); return cur.lastrowid
def interactive():
 raw={}; defaults={"status":"open","fees":"0","reviewed":"no"}
 print("Enter trade fields; blank leaves optional fields empty.")
 for f in COLS:
  v=input("{}{}: ".format(f, " ["+defaults[f]+"]" if f in defaults else "")).strip(); raw[f]=v or defaults.get(f,"")
 return normalize(raw)
def json_rows(obj):
 if isinstance(obj,list): return [x for x in obj if isinstance(x,dict)]
 if isinstance(obj,dict):
  for k in ("trades","trade journal","data","rows","results","items"):
   if isinstance(obj.get(k),list): return [x for x in obj[k] if isinstance(x,dict)]
  return [obj]
 raise ValueError("JSON must be an object or list")
def import_rows(path, fmt):
 if path=="-": raw=sys.stdin.read(); name="stdin."+(fmt or "csv")
 else: p=Path(path); raw=p.read_text(encoding="utf-8-sig"); name=p.name.lower()
 fmt=fmt or ("json" if name.endswith(".json") else "csv")
 return json_rows(json.loads(raw)) if fmt=="json" else list(csv.DictReader(raw.splitlines()))
def records(c): return [{f:r[f] for f in ALL} for r in c.execute("SELECT {} FROM trades ORDER BY id".format(",".join(ALL)))]
def add(c,payload):
 if payload is None: t=interactive()
 else:
  if payload=="-": payload=sys.stdin.read()
  elif payload.startswith("@"): payload=Path(payload[1:]).read_text(encoding="utf-8-sig")
  t=normalize(json.loads(payload))
 ident=insert(c,t); c.commit(); print("Added trade {}.".format(ident)); return 0
def do_import(c,path,fmt):
 ok=0; bad=[]
 for i,row in enumerate(import_rows(path,fmt),1):
  try: insert(c,normalize(row),True); ok+=1
  except (ValueError,sqlite3.Error,TypeError) as e: bad.append("row {}: {}".format(i,e))
 c.commit(); print("Imported {}; skipped {}.".format(ok,len(bad)))
 for e in bad: print(e,file=sys.stderr)
 return 1 if bad and not ok else 0
def do_export(c,fmt,out):
 rows=records(c); fmt=fmt or ("json" if out and out.lower().endswith(".json") else "csv")
 if fmt=="json": rendered=json.dumps(rows,ensure_ascii=False,indent=2)+"\n"
 else:
  b=io.StringIO(newline=""); w=csv.DictWriter(b,fieldnames=ALL,lineterminator="\n"); w.writeheader(); w.writerows(rows); rendered=b.getvalue()
 if out: p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(rendered,encoding="utf-8"); print("Exported {} trades to {}.".format(len(rows),p))
 else: sys.stdout.write(rendered)
 return 0
def pct(a,b): return 100*a/b if b else 0.0
def report(c):
 rows=records(c); closed=[r for r in rows if r["status"]!="open" or r["net_pnl"] is not None]; pnl=[float(r["net_pnl"]) for r in closed if r["net_pnl"] is not None]; wins=[x for x in pnl if x>0]; losses=[x for x in pnl if x<0]; net=sum(pnl); fees=sum(float(r["fees"] or 0) for r in rows); pf=sum(wins)/abs(sum(losses)) if losses else (float("inf") if wins else 0.0)
 days={}
 for r in closed:
  if r["net_pnl"] is not None and (r["exit_time"] or r["entry_time"]): days[str(r["exit_time"] or r["entry_time"])[:10]]=days.get(str(r["exit_time"] or r["entry_time"])[:10],0)+float(r["net_pnl"])
 daypct=pct(sum(v>0 for v in days.values()),len(days)); exp=net/len(pnl) if pnl else 0; reviewed=pct(sum(bool(r["reviewed"]) for r in closed),len(closed)); pfscore=100 if pf==float("inf") else (100*pf/(pf+1) if pf else 0); eq=100 if exp>0 else 50 if exp==0 else 0; edge=(.35*pct(len(wins),len(pnl))+.25*pfscore+.20*daypct+.10*reviewed+.10*eq) if pnl else 0
 print("KYLA Trading Journal Report\n----------------------------")
 print("Net P&L:       {:.2f}".format(net)); print("Trade win %:   {:.2f}%".format(pct(len(wins),len(pnl)))); print("Profit factor: {}".format("inf" if pf==float("inf") else "{:.2f}".format(pf))); print("Day win %:     {:.2f}%".format(daypct)); print("Average win:   {:.2f}".format(sum(wins)/len(wins) if wins else 0)); print("Average loss:  {:.2f}".format(sum(losses)/len(losses) if losses else 0)); print("Trade count:   {} ({} closed, {} open)".format(len(rows),len(closed),len(rows)-len(closed))); print("Total fees:    {:.2f}".format(fees)); print("Expectancy:    {:.2f} per closed trade".format(exp)); print("KYLA Edge:     {:.2f}/100".format(edge)); return 0
def main(argv=None):
 p=argparse.ArgumentParser(description="Network-free SQLite trading journal"); p.add_argument("--db",default=str(DEFAULT_DB),help="SQLite path (default: journal/trades.db)"); s=p.add_subparsers(dest="command")
 a=s.add_parser("add",help="add interactively or with --json"); a.add_argument("--json",dest="payload",metavar="JSON",help="object, @FILE, or - for stdin")
 i=s.add_parser("import",help="import CSV/JSON, including common LuxAlgo headers"); i.add_argument("file"); i.add_argument("--format",choices=("csv","json"))
 r=s.add_parser("report",help="show KPIs")
 e=s.add_parser("export",help="backup as CSV or JSON"); e.add_argument("--format",choices=("csv","json")); e.add_argument("--output","-o")
 a=p.parse_args(argv)
 if not a.command: p.print_help(); return 2
 c=connect(a.db)
 try:
  if a.command=="add": return add(c,a.payload)
  if a.command=="import": return do_import(c,a.file,a.format)
  if a.command=="report": return report(c)
  return do_export(c,a.format,a.output)
 except (OSError,ValueError,json.JSONDecodeError,csv.Error,sqlite3.Error) as e:
  print("error: {}".format(e),file=sys.stderr); return 2
 finally: c.close()
if __name__=="__main__": sys.exit(main())
