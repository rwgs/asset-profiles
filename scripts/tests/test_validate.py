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
