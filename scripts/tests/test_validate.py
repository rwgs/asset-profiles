"""Tests for `scripts/validate.py`, the only gate the pipeline has."""

from __future__ import annotations

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
