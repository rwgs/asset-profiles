"""Shared fixtures for the pipeline tests.

`scripts/` is not a package: `build.py` puts it on `sys.path` at import time so
that `import normalize` resolves when the pipeline runs as a script. Do the same
here, so the tests import the modules by the same path the build does.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def stock_record() -> dict:
    """A stock record in the shape `normalize_stock` emits, and one that validates."""
    return {
        "schema_version": "1.0.0",
        "kind": "stock",
        "isin": "US0378331005",
        "primary_symbol": "AAPL",
        "listings": [{"symbol": "AAPL", "exchange_mic": "XNAS", "currency": "USD"}],
        "name": "Apple Inc.",
        "sector": "Technology",
        "industry_group": "Hardware",
        "industry": "Consumer Electronics",
        "country": "United States",
        "country_code": "US",
        "website": "https://www.apple.com",
        "summary": "Designs, manufactures and markets consumer electronics.",
        "market_cap_band": "Mega Cap",
        "identifiers": {"isin": "US0378331005", "cusip": "037833100"},
        "provenance": {
            "source": "FinanceDatabase",
            "source_url": "https://github.com/JerBouma/FinanceDatabase",
            "fetched_at": "2026-05-31T04:12:00Z",
            "license": "MIT",
        },
    }


@pytest.fixture
def etf_record() -> dict:
    """An ETF record in the shape `normalize_etf` emits, and one that validates."""
    return {
        "schema_version": "1.0.0",
        "kind": "etf",
        "primary_symbol": "SPY",
        "listings": [{"symbol": "SPY", "exchange_mic": "ARCX", "currency": "USD"}],
        "name": "SPDR S&P 500 ETF Trust",
        "issuer": "State Street Global Advisors",
        "as_of_date": "2026-04-30",
        "sector_weights": [
            {"sector": "Technology", "weight": 0.6},
            {"sector": "Financials", "weight": 0.4},
        ],
        "country_weights": [{"country": "United States", "country_code": "US", "weight": 1.0}],
        "asset_class_weights": [{"asset_class": "Equity", "weight": 1.0}],
        "top_holdings": [
            {"symbol": "AAPL", "isin": "US0378331005", "name": "Apple Inc.", "weight": 0.07},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "weight": 0.06},
        ],
        "holdings_count": 503,
        "provenance": {
            "source": "SEC EDGAR N-PORT",
            "source_url": "https://www.sec.gov/Archives/edgar/data/884394/000088439426000042/primary_doc.xml",
            "fetched_at": "2026-05-31T04:12:00Z",
            "license": "Public domain (17 USC 105)",
        },
    }


@pytest.fixture
def index_of():
    """Build the smallest index `index.schema.json` accepts, naming one stock
    shard by both its symbol and its ISIN. `stocks` is the count the index
    claims, which the validator checks against the files actually on disk.
    `also` names further shard paths, each keyed in `symbols` by the shard key
    its path implies -- which is what `build_index` does."""

    def build(isin: str, *, stocks: int, also: Iterable[str] = ()) -> dict:
        path = f"stocks/{isin}.json"
        symbols = {"AAPL": {"kind": "stock", "path": path, "isin": isin}}
        for extra in also:
            symbols[extra[len("stocks/"):-len(".json")]] = {"kind": "stock", "path": extra}
        return {
            "schema_version": "1.0.0",
            "generated_at": "2026-05-31T04:12:00Z",
            "next_refresh_at": "2026-06-07T04:12:00Z",
            "counts": {"stocks": stocks, "etfs": 0},
            "symbols": symbols,
            "isins": {isin: path},
        }

    return build
