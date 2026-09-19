#!/usr/bin/env python3
"""Diagnose why the SOL micro-scalper emits few or no raw signals.

This script deliberately uses only the Python standard library for HTTP/JSON and
imports the repository's stdlib-only SolMicroScalp. It downloads about 5,000
SOLUSDT spot 5-minute candles in Binance API-sized pages, then feeds every
candle to the strategy with funding_rate=0.0.

The rejection counters mirror the actual order and conditions in
quant/strategies/sol_micro_scalp.py. The source has no time-of-day or volume
filter, so those two counters are intentionally always zero; they are printed
so a caller does not mistake an absent filter for a passing filter. The
strategy's ATR fallback is the mean of the previous up-to-14 true candle
ranges (in this source it is simply high-low), and its previous candle state is
updated even when an earlier filter rejects the current candle.

This is a signal diagnostic, not a fill/backtest: it does not apply stops,
targets, max-hold exits, fees, or Backtester's position handling. Binance spot
candles are used because the public endpoint is dependency-free; the strategy
itself is labeled for futures, and funding is neutralized by the requested
0.0 value.
"""

import ssl
import urllib.request

# Demo-only for Mel's Catalina box; real use should verify certificates.
ctx = ssl._create_unverified_context()
urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx)))

import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from quant.strategies.sol_micro_scalp import Config, SolMicroScalp

API_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "SOLUSDT"
INTERVAL = "5m"
PAGE_SIZE = 1000
TARGET_CANDLES = 5000

def fetch_page(end_time=None):
    params = {"symbol": SYMBOL, "interval": INTERVAL, "limit": PAGE_SIZE}
    if end_time is not None:
        params["endTime"] = str(end_time)
    url = API_URL + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "kyla-quant-sol-scalp-diag/1.0"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if isinstance(payload, dict):
        raise RuntimeError("Binance returned an error: {}".format(payload))
    if not isinstance(payload, list):
        raise RuntimeError("Binance returned an unexpected kline payload")
    return payload

def load_recent_klines():
    """Page backward by open time, then return the newest TARGET_CANDLES rows."""
    rows_by_open_time = {}
    end_time = None
    while len(rows_by_open_time) < TARGET_CANDLES:
        page = fetch_page(end_time)
        if not page:
            break
        before = len(rows_by_open_time)
        for row in page:
            if len(row) >= 6:
                rows_by_open_time[int(row[0])] = row
        if len(rows_by_open_time) == before:
            raise RuntimeError("Binance pagination made no progress")
        oldest_open_time = min(int(row[0]) for row in page)
        end_time = oldest_open_time - 1
        if len(page) < PAGE_SIZE:
            break
        # Stay well below the public endpoint's request-rate limits.
        time.sleep(0.10)

    rows = [rows_by_open_time[key] for key in sorted(rows_by_open_time)]
    return rows[-TARGET_CANDLES:]

def candle_from_row(row):
    # This mapping intentionally matches the fields accepted by SolMicroScalp:
    # timestamp/open/high/low/close plus funding_rate. Values are numeric,
    # and timestamp is an aware UTC datetime accepted by the strategy's _ts().
    return {
        "timestamp": datetime.fromtimestamp(int(row[0]) / 1000.0, tz=timezone.utc),
        "open": float(row[1]),
        "high": float(row[2]),
        "low": float(row[3]),
        "close": float(row[4]),
        "volume": float(row[5]),
        "funding_rate": 0.0,
    }

def expected_rejection(strategy, candle):
    """Return the first source-level entry gate rejecting this candle.

    This is evaluated immediately before strategy.next(), while strategy state
    still represents the prior candle. It intentionally follows next():
    funding, dump flags, ATR compression, previous-candle warmup, then the
    one-candle breakout/body-direction momentum test.
    """
    config = strategy.config
    funding = candle.get("funding_rate", candle.get("funding"))
    if funding is None or abs(float(funding)) > config.max_abs_funding:
        return "funding"

    dump_keys = ("btc_dump", "btc_candle_dump", "btc_dump_flag")
    if any(bool(candle.get(key, False)) for key in dump_keys):
        return "bts_dump_flag"

    explicit_atr_compressed = candle.get("atr_compressed")
    atr = candle.get("atr")
    if atr is None:
        recent_ranges = strategy.ranges[-14:]
        atr = (sum(recent_ranges) / len(recent_ranges)
               if recent_ranges else candle["high"] - candle["low"])
    compressed = (bool(explicit_atr_compressed)
                  if explicit_atr_compressed is not None
                  else float(atr) <= candle["close"] * config.min_atr_fraction)
    if compressed:
        return "atr_compressed"

    previous = strategy.previous
    if previous is None:
        return "warmup_previous"

    previous_high = float(previous["high"])
    previous_low = float(previous["low"])
    bullish_breakout = (candle["close"] > previous_high
                        and candle["close"] > candle["open"])
    bearish_breakout = (candle["close"] < previous_low
                        and candle["close"] < candle["open"])
    if not (bullish_breakout or bearish_breakout):
        return "momentum"
    return None

def diagnose(rows):
    strategy = SolMicroScalp(Config())
    counts = Counter({
        "time_of_day": 0,
        "volume": 0,
        "funding": 0,
        "bts_dump_flag": 0,
        "atr_compressed": 0,
        "warmup_previous": 0,
        "momentum": 0,
        "strategy_no_signal": 0,
        "unexpected_signal": 0,
    })
    long_signals = 0
    short_signals = 0
    mirror_mismatches = 0

    for row in rows:
        candle = candle_from_row(row)
        expected = expected_rejection(strategy, candle)
        signal = strategy.next(candle)
        action = getattr(signal, "action", None) if signal is not None else None

        if action == "long":
            long_signals += 1
        elif action == "short":
            short_signals += 1
        elif signal is None:
            if expected is None:
                counts["strategy_no_signal"] += 1
                mirror_mismatches += 1
            else:
                counts[expected] += 1
        else:
            counts["unexpected_signal"] += 1
            mirror_mismatches += 1

        if signal is not None and expected is not None:
            mirror_mismatches += 1

    return counts, long_signals, short_signals, mirror_mismatches

def main():
    try:
        rows = load_recent_klines()
    except Exception as exc:
        print("download failed: {}".format(exc), file=sys.stderr)
        return 1
    if not rows:
        print("download returned no candles", file=sys.stderr)
        return 1

    counts, long_signals, short_signals, mismatches = diagnose(rows)
    first = datetime.fromtimestamp(int(rows[0][0]) / 1000.0, tz=timezone.utc)
    last = datetime.fromtimestamp(int(rows[-1][0]) / 1000.0, tz=timezone.utc)

    print("SOLUSDT 5m SolMicroScalp diagnostics")
    print("candles_seen: {} ({} to {})".format(len(rows), first.isoformat(), last.isoformat()))
    print("long_signals: {}".format(long_signals))
    print("short_signals: {}".format(short_signals))
    print("rejections: time_of_day={} volume={} funding={} bts_dump_flag={} "
          "atr_compressed={} warmup_previous={} momentum={}".format(
              counts["time_of_day"], counts["volume"], counts["funding"],
              counts["bts_dump_flag"], counts["atr_compressed"],
              counts["warmup_previous"], counts["momentum"]))
    print("diagnostic_mismatches: {} (expected zero; mirror-vs-next sanity check)".format(mismatches))
    print("config: min_atr_fraction={} max_abs_funding={} max_hold_minutes={}".format(
        Config().min_atr_fraction, Config().max_abs_funding, Config().max_hold_minutes))
    print("notes: source has no time-of-day or volume filter; funding_rate was forced to 0.0.")
    print("notes: momentum means close broke the immediately previous candle high/low "
          "and the candle body agreed; ATR compression and BTC-dump flags are exact source gates.")
    print("notes: spot candles and neutral funding diagnose raw signals only; this is not a "
          "futures fill/backtest and does not count trades or apply hold/exit behavior.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
