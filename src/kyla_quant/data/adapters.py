"""Safe, documented boundaries for market and macro data sources.

These adapters intentionally return placeholders/errors rather than pretending that
credentials, vendor schemas, or production reliability have been implemented.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class AdapterResult:
    """A source response with explicit freshness and venue metadata."""

    source: str
    venue: str
    received_at: datetime
    records: list[Mapping[str, Any]]
    complete: bool = False
    error: str | None = None


class AdapterStub:
    """Base class for a fail-closed adapter stub."""

    source = "placeholder"
    venue = "placeholder"

    def fetch(self, **_: Any) -> AdapterResult:
        return AdapterResult(
            source=self.source,
            venue=self.venue,
            received_at=datetime.now(timezone.utc),
            records=[],
            complete=False,
            error="TODO: implement and integration-test this adapter with real credentials",
        )


class OandaV20PracticeAdapter(AdapterStub):
    source, venue = "oanda_v20_practice", "oanda_practice"


class BinanceAdapter(AdapterStub):
    """Boundary for klines, funding, and open-interest endpoints."""

    source, venue = "binance_klines_funding_oi", "binance"


class HyperliquidAdapter(AdapterStub):
    source, venue = "hyperliquid", "hyperliquid"


class YFinanceResearchAdapter(AdapterStub):
    source, venue = "yfinance_research_only", "yfinance"


class FREDAdapter(AdapterStub):
    source, venue = "fred_macro", "fred"


class BLSAdapter(AdapterStub):
    """Boundary for CPI/NFP series; do not assume release timing or revision policy."""

    source, venue = "bls_cpi_nfp", "bls"


class FOMCCalendarAdapter(AdapterStub):
    source, venue = "fomc_calendar", "fomc"
