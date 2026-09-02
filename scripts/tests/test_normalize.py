"""Tests for `scripts/normalize.py`."""

from __future__ import annotations

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


@pytest.mark.parametrize("key", ["US0378331005", "AAPL", "BRK-A", "VOD.L", "BMW.DE"])
def test_shard_key_returns_a_well_formed_key_unchanged(key):
    """Escaping applied more broadly than the filesystem requires would rename
    98,000 shards and break every client-cached path, so pin the identity case."""
    assert normalize.shard_key({"primary_symbol": key}) == key


# The two upstream keys the filesystem refuses. Both are known-failing here:
# `strict` means that the day the fix lands these are reported as unexpected
# passes, and get turned into plain assertions in the same change.


@pytest.mark.xfail(strict=True, reason="TASKS.md T6: a separator in a key still becomes a directory")
@pytest.mark.parametrize("key", ["BRK/A", "BF/A", "AKO/B", "RAC/WS", "BIO/B"])
def test_shard_key_is_a_single_path_component(key):
    assert "/" not in normalize.shard_key({"primary_symbol": key})


@pytest.mark.xfail(strict=True, reason="PR #5: a DOS device name in a key still reaches the filesystem")
@pytest.mark.parametrize("key", ["CON", "CON.DE"])
def test_shard_key_escapes_a_dos_device_name(key):
    stem = normalize.shard_key({"primary_symbol": key}).split(".")[0]
    assert stem.upper() not in DOS_DEVICE_NAMES


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
