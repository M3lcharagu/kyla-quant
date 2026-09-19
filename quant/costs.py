"""Pure-Python trading-cost helpers.

Spread is a full quoted round-trip bid/ask difference; slippage and commission
are per-side. Values are price/quote units per quantity unless noted.
"""
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass(frozen=True)
class InstrumentCost:
    symbol: str
    spread: Optional[float]
    spread_unit: str
    commission_per_side: float = 0.0
    commission_rate_per_side: float = 0.0
    slippage_per_side: float = 0.0
    point_value: float = 1.0
    notes: str = ""

DEFAULT_COSTS: Dict[str, InstrumentCost] = {
    "GBPUSD": InstrumentCost("GBPUSD", 1.6, "pips", notes="Initial; measure by session and venue."),
    "USDJPY": InstrumentCost("USDJPY", 1.6, "pips", notes="Initial; measure by session and venue."),
    "GBPJPY": InstrumentCost("GBPJPY", 3.45, "pips", notes="Initial; measure by session and venue."),
    "XAUUSD": InstrumentCost("XAUUSD", None, "price units", notes="TBD-measure before trusting results."),
    "NAS100_OANDA": InstrumentCost("NAS100_OANDA", 1.1, "points", point_value=20.0, notes="OANDA: 1.1pt on $20/point; verify."),
    "BINANCE_SOL_SPOT": InstrumentCost("BINANCE_SOL_SPOT", None, "price units", commission_rate_per_side=0.001, notes="Taker 0.10%/side; check BNB discount."),
    "BINANCE_SOL_FUTURES": InstrumentCost("BINANCE_SOL_FUTURES", None, "price units", commission_rate_per_side=0.0005, notes="Taker 0.05%/side; check BNB discount."),
    "BINANCE_SOL_MAKER": InstrumentCost("BINANCE_SOL_MAKER", None, "price units", commission_rate_per_side=0.0002, notes="Maker 0.02%/side; check BNB discount."),
}

def calculate_all_in_cost(*, spread: Optional[float], quantity: float = 1.0,
                          slippage_per_side: float = 0.0,
                          commission_per_side: float = 0.0,
                          notional_per_side: Optional[float] = None,
                          commission_rate_per_side: float = 0.0) -> float:
    """Return spread + two-sided slippage + two-sided commission."""
    if spread is None:
        raise ValueError("spread must be measured before calculating all-in cost")
    if any(x < 0 for x in (spread, quantity, slippage_per_side, commission_per_side, commission_rate_per_side)):
        raise ValueError("cost and quantity inputs cannot be negative")
    if commission_rate_per_side and notional_per_side is None:
        raise ValueError("notional_per_side is required for percentage commission")
    percentage = 2 * (notional_per_side or 0.0) * commission_rate_per_side
    return spread * quantity + 2 * slippage_per_side * quantity + 2 * commission_per_side + percentage

def instrument_round_trip_cost(model: InstrumentCost, *, quantity: float = 1.0,
                               notional_per_side: Optional[float] = None) -> float:
    return calculate_all_in_cost(spread=model.spread, quantity=quantity,
        slippage_per_side=model.slippage_per_side, commission_per_side=model.commission_per_side,
        notional_per_side=notional_per_side, commission_rate_per_side=model.commission_rate_per_side)

def break_even_probability(cost_r: float, target_r: float) -> float:
    """Symmetric-target/stop break-even: p_BE = 0.5 + C/(2T)."""
    if cost_r < 0 or target_r <= 0:
        raise ValueError("cost_r must be non-negative and target_r positive")
    return 0.5 + cost_r / (2 * target_r)

p_BE = break_even_probability

def get_default_cost(symbol: str) -> InstrumentCost:
    try:
        return DEFAULT_COSTS[symbol]
    except KeyError as exc:
        raise KeyError("no default cost model for {!r}".format(symbol)) from exc
