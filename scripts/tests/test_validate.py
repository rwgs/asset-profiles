"""Tests for `scripts/validate.py`, the only gate the pipeline has."""

from __future__ import annotations

import json

import pytest

import validate


def test_a_generated_stock_record_validates(stock_record):
    assert validate.validate_record(stock_record) == []


def test_a_generated_etf_record_validates(etf_record):
    assert validate.validate_record(etf_record) == []


def test_an_unknown_kind_is_rejected(stock_record):
    stock_record["kind"] = "bond"
    with pytest.raises(validate.ValidationError):
        validate.validate_record(stock_record)


def test_a_missing_required_field_is_an_error(stock_record):
    del stock_record["name"]
    errors = validate.validate_record(stock_record)
    assert [e for e in errors if e.startswith("schema:") and "name" in e]


def test_an_unexpected_field_is_an_error(stock_record):
    # Quotes are out of scope for this dataset, so the schema must refuse one.
    stock_record["price"] = 213.5
    errors = validate.validate_record(stock_record)
    assert [e for e in errors if e.startswith("schema:") and "price" in e]


def test_a_malformed_isin_is_an_error(stock_record):
    stock_record["isin"] = "NOT-AN-ISIN"
    errors = validate.validate_record(stock_record)
    assert [e for e in errors if e.startswith("schema:") and "isin" in e]


@pytest.mark.parametrize("field", ["sector_weights", "country_weights", "asset_class_weights"])
def test_weights_that_do_not_sum_to_one_are_an_error(etf_record, field):
    etf_record[field] = [{**etf_record[field][0], "weight": 0.5}]
    errors = validate.validate_record(etf_record)
    assert [e for e in errors if e.startswith(f"weights: {field} sums to 0.5000")]


def test_a_weight_sum_inside_the_tolerance_passes(etf_record):
    etf_record["asset_class_weights"] = [{"asset_class": "Equity", "weight": 0.997}]
    assert validate.validate_record(etf_record) == []


def test_an_absent_weighted_list_is_not_a_weight_error(etf_record):
    """A missing field means unknown, not zero, so omitting one must validate."""
    del etf_record["country_weights"]
    assert validate.validate_record(etf_record) == []


def test_top_holdings_summing_over_one_are_an_error(etf_record):
    etf_record["top_holdings"] = [
        {"symbol": "AAPL", "weight": 0.6},
        {"symbol": "MSFT", "weight": 0.5},
    ]
    errors = validate.validate_record(etf_record)
    assert [e for e in errors if "top_holdings" in e]


# ---- platform independence ----------------------------------------------
#
# The validator is the whole gate, and it runs on a contributor's machine as
# well as on the Linux runner. Both halves of its text handling used to inherit
# the host locale: it read shards with no encoding, and it wrote characters a
# cp1252 console cannot encode. Keep the fixtures below escaped rather than
# literal, so this file stays ASCII and a failure here can be reported on the
# same console it is about.


def test_a_record_the_host_locale_cannot_decode_still_validates(tmp_path, stock_record, index_of):
    """A Japanese name carries byte 0x8F, which cp1252 has no mapping for, so
    reading a shard without an explicit encoding fails on a Windows host and
    passes on the runner. Records are UTF-8 wherever they are read."""
    stock_record["name"] = "\u30bd\u30cb\u30fc\u30b0\u30eb\u30fc\u30d7\u682a\u5f0f\u4f1a\u793e"
    (tmp_path / "stocks").mkdir()
    shard = tmp_path / "stocks" / "US0378331005.json"
    shard.write_text(json.dumps(stock_record, ensure_ascii=False), encoding="utf-8")
    assert b"\x8f" in shard.read_bytes(), "fixture no longer carries the undecodable byte"

    (tmp_path / "index.json").write_text(
        json.dumps(index_of("US0378331005", stocks=1)), encoding="utf-8"
    )
    assert validate.validate_tree(tmp_path) == 0


def test_every_message_the_validator_writes_itself_is_ascii(tmp_path, etf_record, index_of):
    """The report goes to whatever stdout the host supplies, so one non-ASCII
    character in a message template aborts the run mid-report, losing the
    findings already printed. Record values may be non-ASCII; templates may not."""
    etf_record["asset_class_weights"] = [{"asset_class": "Equity", "weight": 0.5}]
    etf_record["top_holdings"] = [
        {"symbol": "AAPL", "weight": 0.6},
        {"symbol": "MSFT", "weight": 0.5},
    ]
    messages = validate.validate_record(etf_record)
    messages += validate.validate_index(index_of("US0378331005", stocks=0), tmp_path)

    assert messages, "fixture produced no diagnostics to inspect"
    assert [m for m in messages if not m.isascii()] == []


# ---- reachability --------------------------------------------------------
#
# A shard is reachable only if `index.json` names it: the client contract
# resolves a symbol or ISIN through the index and never guesses a filename. So a
# file on disk that the index does not name is invisible to every consumer, and
# one nested in a directory is invisible to the gate as well, because a key
# containing a path separator makes `build.py` create the directory. Three
# quantities have to agree -- the count the index claims, the files on disk, and
# the distinct paths the index names -- and the validator used to check only
# that every path it named existed.


def _write(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")


def _keyed_by_symbol(record, symbol):
    """A copy keyed by symbol rather than ISIN, which is how every nested record
    in `v1/` arises: `group_cross_listings` merges by ISIN, so a row carrying
    none keeps its symbol as the shard key and the separator reaches the path."""
    out = {k: v for k, v in record.items() if k != "isin"}
    out["primary_symbol"] = symbol
    out["listings"] = [{**record["listings"][0], "symbol": symbol}]
    return out


@pytest.mark.parametrize("orphan", ["stocks/ORPHAN.json", "stocks/BRK/A.json"])
def test_a_shard_the_index_does_not_name_is_an_error(tmp_path, stock_record, index_of, orphan):
    """Flat or nested, a record no index entry points at cannot be read by a
    client. `BRK/A` is the real case: nine such directories exist in `v1/`."""
    _write(tmp_path / "stocks" / "US0378331005.json", stock_record)
    _write(tmp_path / orphan, _keyed_by_symbol(stock_record, "ORPHAN"))

    errors = validate.validate_index(index_of("US0378331005", stocks=1), tmp_path)
    assert [e for e in errors if orphan in e and "not named by the index" in e]


def test_a_nested_shard_is_validated_against_the_schema(
    tmp_path, stock_record, index_of, capsys
):
    """The 13 nested records in `v1/` happen to be schema-valid, so the defect
    is a check that never ran rather than an error that was hidden. This tree
    holds an invalid one, and the index names both shards with a truthful count,
    so the schema error is the only thing left to report. Assert on the report
    rather than the count: a one-level glob makes the count wrong by exactly one
    too, and a test that accepts either passes for the wrong reason."""
    _write(tmp_path / "stocks" / "US0378331005.json", stock_record)
    nested = _keyed_by_symbol(stock_record, "BRK/A")
    del nested["name"]
    _write(tmp_path / "stocks" / "BRK" / "A.json", nested)
    (tmp_path / "index.json").write_text(
        json.dumps(index_of("US0378331005", stocks=2, also=["stocks/BRK/A.json"])),
        encoding="utf-8",
    )

    errors = validate.validate_tree(tmp_path)
    report = capsys.readouterr().out.splitlines()
    assert [line for line in report if "A.json" in line and "schema:" in line], report
    assert errors == 1


def test_a_count_agreeing_with_neither_disk_nor_index_reports_all_three(
    tmp_path, stock_record, index_of
):
    """Two of the three can agree while the third does not, so a message naming
    one comparison tells a reader the wrong thing about which is wrong. `v1/`
    today claims 98,464, holds 98,477, and names 98,463."""
    _write(tmp_path / "stocks" / "US0378331005.json", stock_record)
    _write(tmp_path / "stocks" / "ORPHAN.json", _keyed_by_symbol(stock_record, "ORPHAN"))

    errors = validate.validate_index(index_of("US0378331005", stocks=3), tmp_path)
    counts = [e for e in errors if e.startswith("index: counts.stocks=3")]
    assert counts, errors
    assert "2 file" in counts[0] and "1 path" in counts[0]


def test_a_tree_whose_three_quantities_agree_passes(tmp_path, stock_record, index_of):
    """The reconciliation must not fire on a tree that is internally consistent,
    including one whose shard is nested: nesting is what T6 repairs, and until
    then a nested record the index names is reachable and has to pass."""
    _write(tmp_path / "stocks" / "US0378331005.json", stock_record)
    _write(tmp_path / "stocks" / "BRK" / "A.json", _keyed_by_symbol(stock_record, "BRK/A"))
    (tmp_path / "index.json").write_text(
        json.dumps(index_of("US0378331005", stocks=2, also=["stocks/BRK/A.json"])),
        encoding="utf-8",
    )

    assert validate.validate_tree(tmp_path) == 0


# ---- shard names ---------------------------------------------------------
#
# `normalize.shard_key` escapes a DOS device name before it becomes a path, so
# a hit here means a record reached disk without going through it. That is
# worth a standing check rather than a one-off: 83,764 of 98,489 shards take
# their filename straight from an upstream ticker refreshed weekly, so the next
# `PRN` or `COM1` listing is a data event, not a code change.


@pytest.mark.parametrize("name", ["CON.json", "CON.DE.json", "prn.json", "COM3.L.json"])
def test_a_reserved_device_name_on_disk_is_an_error(tmp_path, stock_record, name):
    _write(tmp_path / "stocks" / name, stock_record)
    errors = validate.validate_shard_names(tmp_path)
    assert [e for e in errors if "reserved device name" in e and name in e], errors


def test_a_reserved_name_in_a_directory_component_is_an_error(tmp_path, stock_record):
    """A key is escaped per component so `CON/A` cannot create a reserved
    directory. Check the whole path, not just the filename, or the directory
    that breaks the clone is the one the check walks straight past."""
    _write(tmp_path / "stocks" / "CON" / "A.json", stock_record)
    errors = validate.validate_shard_names(tmp_path)
    assert [e for e in errors if "reserved device name" in e], errors


@pytest.mark.parametrize("name", ["CON_.json", "CON_.DE.json", "CONE.json", "AAPL.json"])
def test_an_escaped_or_unrelated_name_passes(tmp_path, stock_record, name):
    _write(tmp_path / "stocks" / name, stock_record)
    assert validate.validate_shard_names(tmp_path) == []


def test_a_reserved_name_fails_the_tree_and_not_only_the_name_check(
    tmp_path, stock_record, index_of
):
    """The check has to be wired into `validate_tree`, or it is a function
    nothing calls. The record itself is valid and the index names it, so the
    device name is the only thing left to fail on."""
    _write(tmp_path / "stocks" / "US0378331005.json", stock_record)
    _write(tmp_path / "stocks" / "CON.json", stock_record)
    (tmp_path / "index.json").write_text(
        json.dumps(index_of("US0378331005", stocks=2, also=["stocks/CON.json"])),
        encoding="utf-8",
    )
    assert validate.validate_tree(tmp_path) == 1


# ---- country codes ------------------------------------------------------
#
# The schema constrains a code to two upper-case letters, which `XX` satisfies.
# N-PORT filers write it for a holding they do not place, and it reached four
# published records as a country whose display name was also `XX`.


def test_an_unassigned_country_code_is_an_error(stock_record):
    stock_record["country_code"] = "XX"
    errors = validate.validate_record(stock_record)
    assert [e for e in errors if e.startswith("country: country_code:")]


def test_an_unassigned_code_in_country_weights_is_an_error(etf_record):
    etf_record["country_weights"] = [
        {"country": "United States", "country_code": "US", "weight": 0.9},
        {"country": "XX", "country_code": "XX", "weight": 0.1},
    ]
    errors = validate.validate_record(etf_record)
    assert [e for e in errors if e.startswith("country: country_weights/1/country_code:")]


def test_an_absent_country_code_is_not_an_error(etf_record):
    """A weighted country with no code means unplaced, and the schema allows it.

    Named `Taiwan` rather than `Unknown`: the synthetic-share rule below reads
    `Unknown` as the bucket meaning "not resolved", so a fixture using that
    label at weight 1.0 would fail for a different reason than the one under
    test."""
    etf_record["country_weights"] = [
        {"country": "Taiwan", "weight": 0.6},
        {"country": "United States", "country_code": "US", "weight": 0.4},
    ]
    assert validate.validate_record(etf_record) == []


def test_an_assigned_code_that_is_not_us_passes(stock_record):
    """Guard against a check that only recognises the fixture's own code."""
    stock_record["country_code"] = "JE"  # Jersey: assigned, and in the dataset
    assert validate.validate_record(stock_record) == []


# ---- negative weights ---------------------------------------------------
#
# SEC N-PORT reports short positions and derivatives of negative value, so a
# holding can carry a negative `valUSD` and a bucket can aggregate negative.
# `weight` was constrained to [0, 1], which rejected 11 of the 49 US funds in
# the universe outright -- ten at rounding scale and `SH`, an inverse fund, at
# -0.24. The sum-to-1 invariant is what guards the scale, measured across those
# 49 funds to hold within 3e-06.


def test_a_negative_weight_is_allowed(etf_record):
    """`SH` holds -24% of net assets in one asset class. That is the filing."""
    etf_record["asset_class_weights"] = [
        {"asset_class": "Equity", "weight": 1.24},
        {"asset_class": "Derivative-equity", "weight": -0.24},
    ]
    assert validate.validate_record(etf_record) == []


def test_a_weight_slightly_over_one_is_allowed(etf_record):
    """Renormalizing over a total that includes negatives pushes the largest
    bucket just past 1. Measured at 1.000097 on VTV."""
    etf_record["country_weights"] = [
        {"country": "United States", "country_code": "US", "weight": 1.000097},
        {"country": "Canada", "country_code": "CA", "weight": -0.000097},
    ]
    assert validate.validate_record(etf_record) == []


def test_a_negative_top_holding_is_allowed(etf_record):
    etf_record["top_holdings"] = [{"symbol": "SPY", "weight": -0.001062}]
    assert validate.validate_record(etf_record) == []


def test_percent_scale_weights_are_still_rejected(etf_record):
    """The bound that went away was doing this job; the sum invariant must
    still do it, or `31.7` for 31.7% ships silently."""
    etf_record["sector_weights"] = [
        {"sector": "Technology", "weight": 60.0},
        {"sector": "Financials", "weight": 40.0},
    ]
    errors = validate.validate_record(etf_record)
    assert [e for e in errors if e.startswith("weights: sector_weights sums to 100.0000")]


def test_top_holdings_over_one_are_still_rejected_with_a_negative_present(etf_record):
    etf_record["top_holdings"] = [
        {"symbol": "AAPL", "weight": 0.9},
        {"symbol": "MSFT", "weight": 0.9},
        {"symbol": "SPY", "weight": -0.1},
    ]
    errors = validate.validate_record(etf_record)
    assert [e for e in errors if "top_holdings" in e]


def test_a_majority_synthetic_list_is_an_error(etf_record):
    """`BND` published sector weights that were 100% `Unknown`, summing to 1.0
    and passing every check the validator then had."""
    etf_record["sector_weights"] = [{"sector": "Unknown", "weight": 1.0}]
    errors = validate.validate_record(etf_record)
    assert [e for e in errors if e.startswith("synthetic: sector_weights is 100% unresolved")]


def test_a_mostly_resolved_list_is_not_a_synthetic_error(etf_record):
    etf_record["sector_weights"] = [
        {"sector": "Unknown", "weight": 0.002},
        {"sector": "Technology", "weight": 0.998},
    ]
    assert validate.validate_record(etf_record) == []


def test_omitting_the_list_entirely_is_how_a_fund_passes(etf_record):
    """The rule must be satisfiable by omission, or it just fails bond funds."""
    del etf_record["sector_weights"]
    assert validate.validate_record(etf_record) == []
