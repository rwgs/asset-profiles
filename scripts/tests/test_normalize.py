"""Tests for `scripts/normalize.py`."""

from __future__ import annotations

import copy
import json

import pytest

import normalize

# The names a Windows path component may not take, whatever follows the dot.
DOS_DEVICE_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(10)),
    *(f"LPT{i}" for i in range(10)),
}


# ---- shard_key ----------------------------------------------------------


def test_shard_key_prefers_the_isin():
    record = {"isin": "US0378331005", "primary_symbol": "AAPL"}
    assert normalize.shard_key(record) == "US0378331005"


def test_shard_key_falls_back_to_the_symbol():
    assert normalize.shard_key({"primary_symbol": "AAPL"}) == "AAPL"


@pytest.mark.parametrize(
    "key", ["US0378331005", "AAPL", "BRK-A", "VOD.L", "BMW.DE", "CON_.DE"]
)
def test_shard_key_returns_a_well_formed_key_unchanged(key):
    """Escaping applied more broadly than the filesystem requires would rename
    98,000 shards and break every client-cached path, so pin the identity case."""
    assert normalize.shard_key({"primary_symbol": key}) == key


@pytest.mark.parametrize(
    "key,expected",
    [
        ("BRK/A", "BRK_A"),
        ("BF/A", "BF_A"),
        ("AKO/B", "AKO_B"),
        ("RAC/WS", "RAC_WS"),
        ("BIO/B", "BIO_B"),
    ],
)
def test_shard_key_is_a_single_path_component(key, expected):
    """FinanceDatabase publishes share classes with a separator, and the build
    interpolates the key straight into a path -- so `BRK/A` wrote
    `v1/stocks/BRK/A.json`, a record no index named and no check validated.
    Assert the exact key, not just the absence of a separator: the escape has to
    be the one the override filenames and cached client paths agree on."""
    assert normalize.shard_key({"primary_symbol": key}) == expected


def test_shard_key_composes_both_escapes():
    """A component can need both rules. The device escape runs per component and
    the separator escape joins them, so replacing either rule with the other
    shows up here rather than in a Windows checkout six months later."""
    assert normalize.shard_key({"primary_symbol": "CON/A"}) == "CON__A"


@pytest.mark.parametrize(
    "key,expected",
    [
        ("CON", "CON_"),
        ("CON.DE", "CON_.DE"),
        ("PRN", "PRN_"),
        ("NUL.L", "NUL_.L"),
        ("COM1", "COM1_"),
        ("LPT9.PA", "LPT9_.PA"),
        ("con.de", "con_.de"),
    ],
)
def test_shard_key_escapes_a_dos_device_name(key, expected):
    """Windows resolves any component whose part before the first dot is a
    device name to that device, so `CON.DE.json` is the console and the whole
    clone fails there rather than that one record. Escaping is per component
    and case-insensitive, because the filesystem's rule is."""
    assert normalize.shard_key({"primary_symbol": key}) == expected


@pytest.mark.parametrize("key", ["CONE", "CONS.DE", "ICON", "COM", "COM10", "LPTX"])
def test_shard_key_leaves_a_name_that_merely_starts_like_a_device(key):
    """`COM` and `COM10` are not device names and `CONE` is not `CON`, so
    escaping them would change a working path for nothing. 83,764 shards take
    their name straight from an upstream ticker, so the rule has to be exact."""
    assert normalize.shard_key({"primary_symbol": key}) == key


def test_every_escaped_device_name_is_actually_escaped():
    """The list in `normalize` and the list this file checks against are written
    out separately, so walk the whole set rather than a sample of it."""
    for name in DOS_DEVICE_NAMES:
        stem = normalize.shard_key({"primary_symbol": f"{name}.DE"}).partition(".")[0]
        assert stem.upper() not in DOS_DEVICE_NAMES, name


# ---- _aggregate_weights -------------------------------------------------


def test_aggregate_weights_sums_per_value_and_sorts_descending():
    holdings = [
        {"sector": "Financials", "weight": 0.2},
        {"sector": "Technology", "weight": 0.6},
        {"sector": "Financials", "weight": 0.2},
    ]
    assert normalize._aggregate_weights(holdings, "sector") == [
        {"sector": "Technology", "weight": 0.6},
        {"sector": "Financials", "weight": 0.4},
    ]


def test_aggregate_weights_renormalizes_a_partial_sum_to_one():
    """Renormalization is why a passing weight-sum check is not evidence of
    coverage: holdings covering half the fund still come out at 1.0."""
    holdings = [
        {"asset_class": "Equity", "weight": 0.3},
        {"asset_class": "Cash", "weight": 0.2},
    ]
    out = normalize._aggregate_weights(holdings, "asset_class")
    assert out == [
        {"asset_class": "Equity", "weight": 0.6},
        {"asset_class": "Cash", "weight": 0.4},
    ]
    assert sum(w["weight"] for w in out) == pytest.approx(1.0)


def test_aggregate_weights_skips_a_holding_missing_the_value_or_the_weight():
    holdings = [
        {"sector": "Financials", "weight": 0.5},
        {"sector": None, "weight": 0.5},
        {"sector": "Energy"},
    ]
    assert normalize._aggregate_weights(holdings, "sector") == [
        {"sector": "Financials", "weight": 1.0},
    ]


@pytest.mark.parametrize("holdings", [[], [{"sector": "Energy", "weight": 0.0}]])
def test_aggregate_weights_returns_nothing_when_no_weight_is_usable(holdings):
    assert normalize._aggregate_weights(holdings, "sector") == []


# ---- apply_overrides ----------------------------------------------------


def test_apply_overrides_returns_the_record_when_there_is_no_override(tmp_path, stock_record):
    assert normalize.apply_overrides(stock_record, tmp_path) == stock_record


def test_apply_overrides_deep_merges_the_patch(tmp_path, stock_record):
    (tmp_path / "US0378331005.json").write_text(
        json.dumps({"sector": "Consumer Discretionary", "provenance": {"license": "CC-BY-4.0"}}),
        encoding="utf-8",
    )
    merged = normalize.apply_overrides(stock_record, tmp_path)
    assert merged["sector"] == "Consumer Discretionary"
    assert merged["provenance"]["license"] == "CC-BY-4.0"
    # A sibling key the patch does not name survives the merge.
    assert merged["provenance"]["source"] == "FinanceDatabase"
    # The generated record is not mutated in place.
    assert stock_record["sector"] == "Technology"


def test_apply_overrides_replaces_a_list_wholesale(tmp_path, stock_record):
    (tmp_path / "US0378331005.json").write_text(
        json.dumps({"listings": [{"symbol": "APC", "exchange_mic": "XETR"}]}),
        encoding="utf-8",
    )
    merged = normalize.apply_overrides(stock_record, tmp_path)
    assert merged["listings"] == [{"symbol": "APC", "exchange_mic": "XETR"}]


def test_apply_overrides_drops_the_note_key(tmp_path, stock_record):
    (tmp_path / "US0378331005.json").write_text(
        json.dumps({"_note": "why this override exists", "country_code": "IE"}),
        encoding="utf-8",
    )
    merged = normalize.apply_overrides(stock_record, tmp_path)
    assert "_note" not in merged
    assert merged["country_code"] == "IE"


def test_apply_overrides_resolves_a_record_without_an_isin_by_symbol(tmp_path):
    record = {"kind": "stock", "primary_symbol": "VOD.L", "name": "Vodafone"}
    (tmp_path / "VOD.L.json").write_text(
        json.dumps({"name": "Vodafone Group Public Limited Company"}),
        encoding="utf-8",
    )
    merged = normalize.apply_overrides(record, tmp_path)
    assert merged["name"] == "Vodafone Group Public Limited Company"


def test_apply_overrides_keeps_the_record_when_the_override_is_invalid_json(tmp_path, stock_record):
    (tmp_path / "US0378331005.json").write_text("{ not json", encoding="utf-8")
    assert normalize.apply_overrides(stock_record, tmp_path) == stock_record


# ---- holding enrichment -------------------------------------------------
#
# N-PORT carries no sector, so every ETF `sector_weights` entry comes from
# joining a holding to the stock dataset. Each side of that join is narrow in a
# different place: a holding almost always has an ISIN and almost never a
# ticker, while only 15% of stock records carry an ISIN against 17% carrying a
# CUSIP. So all three legs earn their place.


def _stock(**kw) -> dict:
    base = {"sector": "Technology", "country": "United States", "country_code": "US"}
    base.update(kw)
    return base


def test_a_holding_resolves_by_isin():
    h = {"isin": "US0378331005", "weight": 1.0}
    out = normalize._enrich_holding(h, {"US0378331005": _stock()}, {}, {})
    assert out["sector"] == "Technology"


def test_a_holding_resolves_by_ticker_when_the_isin_is_unknown():
    h = {"isin": "US9999999999", "ticker": "AAPL", "weight": 1.0}
    out = normalize._enrich_holding(h, {}, {"AAPL": _stock()}, {})
    assert out["sector"] == "Technology"


def test_a_holding_resolves_by_cusip_when_isin_and_ticker_miss():
    """The leg that matters most in practice: an N-PORT holding carries a CUSIP
    and an ISIN, but the stock record it belongs to often carries only a CUSIP."""
    h = {"isin": "US0378331005", "cusip": "037833100", "weight": 1.0}
    out = normalize._enrich_holding(h, {}, {}, {"037833100": _stock()})
    assert out["sector"] == "Technology"
    assert out["country_code"] == "US"


def test_isin_wins_over_cusip_when_both_resolve():
    h = {"isin": "US0378331005", "cusip": "037833100", "weight": 1.0}
    out = normalize._enrich_holding(
        h,
        {"US0378331005": _stock(sector="Technology")},
        {},
        {"037833100": _stock(sector="Financials")},
    )
    assert out["sector"] == "Technology"


def test_a_holding_that_resolves_nowhere_is_unknown_not_dropped():
    h = {"isin": "US9999999999", "cusip": "999999999", "weight": 1.0}
    out = normalize._enrich_holding(h, {}, {}, {})
    assert out["sector"] == "Unknown"
    assert out["country"] == "Unknown"
    assert out["asset_class"] == "Other"
    assert out["weight"] == 1.0


def test_enrichment_does_not_overwrite_what_the_filing_stated():
    h = {"cusip": "037833100", "country": "Japan", "country_code": "JP", "weight": 1.0}
    out = normalize._enrich_holding(h, {}, {}, {"037833100": _stock()})
    assert out["country_code"] == "JP"
    assert out["sector"] == "Technology"  # absent in the filing, so filled in


# ---- shadowed records ---------------------------------------------------
#
# `build_index` keys `symbols` by symbol and the last writer wins, so a record
# whose every symbol another record also lists reaches the index by no route at
# all. Measured against the live source on 2026-09-03: exactly one record is in
# that state, `SAND`, and it is the gap of one that T4 traced.


def _row(symbol: str, *, isin: str | None = None, **kw) -> dict:
    rec = {
        "kind": "stock",
        "primary_symbol": symbol,
        "listings": [{"symbol": symbol, "exchange_mic": "XNYS"}],
        "name": f"Record {symbol}",
    }
    if isin:
        rec["isin"] = isin
    rec.update(kw)
    return rec


def test_an_isin_less_record_whose_only_symbol_is_claimed_is_absorbed():
    """The `SAND` shape: Sandstorm Gold publishes with an ISIN and without, and
    the ISIN-bearing record already lists `SAND` among its cross-listings."""
    bearing = _row("SAND", isin="CA80013R2063")
    bearing["listings"].append({"symbol": "SSL.TO", "exchange_mic": "XTSE"})
    out = normalize.group_cross_listings([_row("SAND"), bearing])
    assert [r.get("isin") for r in out] == ["CA80013R2063"]


def test_absorbing_fills_a_field_the_isin_bearing_record_lacks():
    shadowed = _row("SAND", website="https://www.sandstormgold.com")
    bearing = _row("SAND", isin="CA80013R2063")
    out = normalize.group_cross_listings([shadowed, bearing])
    assert len(out) == 1
    assert out[0]["isin"] == "CA80013R2063"
    assert out[0]["website"] == "https://www.sandstormgold.com"


def test_an_isin_less_record_with_a_symbol_of_its_own_is_kept():
    """`BIO/B` and `RAC/WS` have no ISIN-bearing alternate, so dropping every
    ISIN-less duplicate would lose the only record of those securities."""
    out = normalize.group_cross_listings([_row("BIO/B"), _row("AAPL", isin="US0378331005")])
    assert sorted(r["primary_symbol"] for r in out) == ["AAPL", "BIO/B"]


def test_a_partially_claimed_record_is_kept():
    """Absorbing it would lose `SSL.DE`, which nothing else lists."""
    shadowed = _row("SAND")
    shadowed["listings"].append({"symbol": "SSL.DE", "exchange_mic": "XETR"})
    out = normalize.group_cross_listings([shadowed, _row("SAND", isin="CA80013R2063")])
    assert len(out) == 2


def test_two_isin_less_records_sharing_a_symbol_are_both_kept():
    """The `ECC` shape -- two upstream rows for one security, neither with an
    ISIN. `build.write_records` reports the second and skips it, so the
    collision is handled there rather than by silently dropping one here."""
    out = normalize.group_cross_listings([_row("ECC"), _row("ECC")])
    assert len(out) == 2


# ---- majority-synthetic lists -------------------------------------------
#
# Everything a holding lookup cannot resolve is bucketed `Unknown` (or `Other`
# for asset class) and then renormalized to 1.0, so a list carrying no signal
# is shaped exactly like one that does. Six of the ten records published before
# 2026-09-03 had `sector_weights` that were 100% `Unknown` at a valid sum.


def test_synthetic_share_reads_the_unknown_bucket():
    ws = [{"sector": "Unknown", "weight": 0.8}, {"sector": "Technology", "weight": 0.2}]
    assert normalize.synthetic_share("sector_weights", ws) == 0.8


def test_synthetic_share_of_asset_class_reads_other():
    ws = [{"asset_class": "Other", "weight": 0.6}, {"asset_class": "Equity", "weight": 0.4}]
    assert normalize.synthetic_share("asset_class_weights", ws) == 0.6


def test_a_majority_unknown_list_is_dropped():
    ws = [{"sector": "Unknown", "weight": 0.8}, {"sector": "Technology", "weight": 0.2}]
    assert normalize._drop_if_synthetic("sector_weights", ws, "BND") == []


def test_a_list_at_the_threshold_is_kept():
    """Exactly half is not a majority, so it survives. The boundary is where a
    threshold is worth a test."""
    ws = [{"sector": "Unknown", "weight": 0.5}, {"sector": "Technology", "weight": 0.5}]
    assert normalize._drop_if_synthetic("sector_weights", ws, "X") == ws


def test_a_mostly_resolved_list_is_kept():
    ws = [{"sector": "Unknown", "weight": 0.002}, {"sector": "Technology", "weight": 0.998}]
    assert normalize._drop_if_synthetic("sector_weights", ws, "SCHD") == ws


def test_an_already_empty_list_stays_empty():
    assert normalize._drop_if_synthetic("sector_weights", [], "X") == []


# ---- instrument identity ------------------------------------------------


def _certificate() -> dict:
    """`v1/stocks/AT0000A2H326.json` as it publishes today: a leveraged
    certificate over Daimler, `kind` stock, wearing Daimler's sector."""
    return {
        "schema_version": "1.0.0",
        "kind": "stock",
        "isin": "AT0000A2H326",
        "primary_symbol": "AT0000A2H326.VI",
        "listings": [{"symbol": "AT0000A2H326.VI", "exchange_mic": "WBAH", "currency": "EUR"}],
        "name": "EGB OE TL.Z./DAIMLER",
        "sector": "Consumer Discretionary",
        "industry_group": "Automobiles & Components",
        "industry": "Automobile Manufacturers",
        "country": "Austria",
        "country_code": "AT",
        "identifiers": {"isin": "AT0000A2H326"},
        "provenance": {"source": "FinanceDatabase", "source_url": "u",
                       "fetched_at": "2026-09-03T00:00:00Z", "license": "MIT"},
    }


def _aar_corp() -> dict:
    """`v1/stocks/CA18452Y1007.json`: AAR Corp. under Clean Air Metals' ISIN."""
    return {
        "schema_version": "1.0.0",
        "kind": "stock",
        "isin": "CA18452Y1007",
        "primary_symbol": "AIR",
        "listings": [{"symbol": "AIR", "exchange_mic": "XNYS", "currency": "USD"}],
        "name": "AAR Corp.",
        "sector": "Industrials",
        "country": "United States",
        "country_code": "US",
        "identifiers": {"isin": "CA18452Y1007", "cusip": "000361105"},
        "provenance": {"source": "FinanceDatabase", "source_url": "u",
                       "fetched_at": "2026-09-03T00:00:00Z", "license": "MIT"},
    }


def test_a_non_equity_is_retyped_and_loses_its_inherited_sector():
    record = _certificate()
    summary = normalize.apply_instrument_identity(
        [record], kind_by_isin={"AT0000A2H326": "debt"}, wrong_isins=set()
    )
    assert record["kind"] == "debt"
    assert "sector" not in record
    assert "industry_group" not in record
    assert "industry" not in record
    # It is still the same instrument, reachable at the same shard.
    assert record["isin"] == "AT0000A2H326"
    assert normalize.shard_key(record) == "AT0000A2H326"
    assert summary == {"isin_dropped": 0, "retyped": 1, "sector_dropped": 1}


def test_a_fund_share_is_retyped_the_same_way():
    record = _certificate() | {"isin": "IE00B4L5Y983", "name": "Some Fund Plc"}
    record["identifiers"] = {"isin": "IE00B4L5Y983"}
    normalize.apply_instrument_identity(
        [record], kind_by_isin={"IE00B4L5Y983": "fund"}, wrong_isins=set()
    )
    assert record["kind"] == "fund"
    assert "sector" not in record


def test_an_equity_is_left_exactly_as_it_was(stock_record):
    before = copy.deepcopy(stock_record)
    summary = normalize.apply_instrument_identity(
        [stock_record], kind_by_isin={"US0378331005": "stock"}, wrong_isins=set()
    )
    assert stock_record == before
    assert summary == {"isin_dropped": 0, "retyped": 0, "sector_dropped": 0}


def test_an_untyped_isin_is_left_exactly_as_it_was(stock_record):
    """OpenFIGI had no answer for 836 of 9,400 published ISINs. Silence must
    not restate a record."""
    before = copy.deepcopy(stock_record)
    normalize.apply_instrument_identity([stock_record], kind_by_isin={}, wrong_isins=set())
    assert stock_record == before


def test_a_wrong_isin_is_dropped_and_the_record_rekeys_by_symbol():
    record = _aar_corp()
    summary = normalize.apply_instrument_identity(
        [record], kind_by_isin={}, wrong_isins={"CA18452Y1007"}
    )
    assert "isin" not in record
    assert record["identifiers"] == {"cusip": "000361105"}
    # The company stays reachable, under a key that is its own.
    assert record["name"] == "AAR Corp."
    assert normalize.shard_key(record) == "AIR"
    assert summary == {"isin_dropped": 1, "retyped": 0, "sector_dropped": 0}


def test_dropping_the_only_identifier_drops_the_empty_block():
    record = _aar_corp()
    record["identifiers"] = {"isin": "CA18452Y1007"}
    normalize.apply_instrument_identity(
        [record], kind_by_isin={}, wrong_isins={"CA18452Y1007"}
    )
    assert "identifiers" not in record


def test_a_dropped_isin_is_never_also_read_for_a_type():
    """The type describes whatever instrument the wrong ISIN identifies, so it
    must not be applied to the record that was wearing it."""
    record = _aar_corp()
    normalize.apply_instrument_identity(
        [record],
        kind_by_isin={"CA18452Y1007": "fund"},
        wrong_isins={"CA18452Y1007"},
    )
    assert record["kind"] == "stock"
    assert record["sector"] == "Industrials"
    assert "isin" not in record


def test_a_record_with_no_isin_is_untouched():
    record = {"kind": "stock", "primary_symbol": "CLRMF", "name": "Clean Air Metals Inc."}
    before = copy.deepcopy(record)
    normalize.apply_instrument_identity(
        [record], kind_by_isin={}, wrong_isins={"CA18452Y1007"}
    )
    assert record == before
