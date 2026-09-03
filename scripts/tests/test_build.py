"""Tests for `scripts/build.py`.

`import build` pulls in the source modules, and through them pandas, requests
and lxml. The rest of this suite deliberately needs only `pycountry` and
`jsonschema`, so that it runs on a host where the full requirements do not
install -- see `TASKS.md` T8. Skip rather than give that up: CI installs the
full requirements, so these run there.
"""

from __future__ import annotations

import json
import logging

import pytest

pytest.importorskip("pandas", reason="build.py imports the source modules")

import build  # noqa: E402


def _keyed_by_symbol(record: dict, symbol: str) -> dict:
    """A copy keyed by symbol rather than ISIN. Only about 15% of stock records
    carry an ISIN, so this is the common shape, and it is the one whose key
    comes straight from an upstream ticker."""
    out = {k: v for k, v in record.items() if k != "isin"}
    out["primary_symbol"] = symbol
    out["listings"] = [{**record["listings"][0], "symbol": symbol}]
    out["name"] = f"Record {symbol}"
    return out


def test_two_records_escaping_to_one_key_are_reported_and_not_overwritten(
    tmp_path, stock_record, caplog
):
    """`BRK/A` escapes to `BRK_A`, which an upstream ticker of `BRK_A` also
    produces. No key in the current data contains `_`, so this cannot happen
    today -- but 83,764 shards take their name straight from a ticker refreshed
    weekly, so it is a measurement of today's data rather than an invariant.
    The failure it guards against is silent: the second record's file would
    replace the first's with no diagnostic anywhere."""
    first = _keyed_by_symbol(stock_record, "BRK/A")
    second = _keyed_by_symbol(stock_record, "BRK_A")
    summary = {"added": 0, "changed": 0, "unchanged": 0, "removed": 0}

    with caplog.at_level(logging.ERROR):
        keys, invalid = build.write_records(
            [first, second], tmp_path, "stock", summary=summary
        )

    assert keys == {"BRK_A"}
    assert invalid == 1
    assert [r for r in caplog.records if "BRK_A" in r.getMessage()], caplog.text

    written = json.loads((tmp_path / "BRK_A.json").read_text(encoding="utf-8"))
    assert written["name"] == "Record BRK/A", "the second record overwrote the first"


def test_a_record_that_fails_validation_is_not_written(tmp_path, stock_record):
    """The gate runs per record during the build, not only over the finished
    tree, so an invalid record must never reach disk in the first place."""
    bad = _keyed_by_symbol(stock_record, "BAD")
    del bad["name"]
    summary = {"added": 0, "changed": 0, "unchanged": 0, "removed": 0}

    keys, invalid = build.write_records([bad], tmp_path, "stock", summary=summary)

    assert keys == set()
    assert invalid == 1
    assert list(tmp_path.rglob("*.json")) == []


def test_a_shard_left_nested_by_the_old_key_is_reaped(tmp_path, stock_record):
    """The 13 records under `v1/stocks/` were written as `BRK/A.json` by the
    unescaped key. Nothing deletes them explicitly: they are reaped because the
    repaired key no longer names them. A `--limit` build into a fresh `--out`
    tree cannot show this, since there is nothing there to reap."""
    stale = tmp_path / "BRK" / "A.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}", encoding="utf-8")
    summary = {"added": 0, "changed": 0, "unchanged": 0, "removed": 0}

    keys, _ = build.write_records(
        [_keyed_by_symbol(stock_record, "BRK/A")], tmp_path, "stock", summary=summary
    )

    assert keys == {"BRK_A"}
    assert not stale.exists(), "the nested shard survived beside its replacement"
    assert (tmp_path / "BRK_A.json").exists()
    assert summary["removed"] == 1


def test_index_stocks_keys_a_record_by_isin_symbol_and_cusip(stock_record):
    by_isin, by_symbol, by_cusip = build._index_stocks([stock_record])
    assert by_isin["US0378331005"] is stock_record
    assert by_symbol["AAPL"] is stock_record
    assert by_cusip["037833100"] is stock_record


def test_index_stocks_keys_a_record_that_carries_only_a_cusip(stock_record):
    """The common shape: 16,519 stock records carry a CUSIP, 14,716 an ISIN."""
    del stock_record["isin"]
    stock_record["identifiers"] = {"cusip": "037833100"}
    by_isin, by_symbol, by_cusip = build._index_stocks([stock_record])
    assert by_isin == {}
    assert by_cusip["037833100"] is stock_record


def test_index_stocks_skips_a_record_with_no_identifiers(stock_record):
    del stock_record["isin"]
    del stock_record["identifiers"]
    by_isin, by_symbol, by_cusip = build._index_stocks([stock_record])
    assert by_isin == {} and by_cusip == {}
    assert by_symbol["AAPL"] is stock_record  # a listing symbol is always there


# ---- ETF coverage report ------------------------------------------------
#
# The build reported `etfs: N valid, M invalid`, under which a universe entry
# could produce nothing without ever being named, and a record whose weights
# are 100% `Unknown` looked identical to one that carries signal. Six of the
# ten published records are in exactly that state.


def _etf(symbol: str, *, unknown: float = 0.0) -> dict:
    return {
        "kind": "etf",
        "primary_symbol": symbol,
        "holdings_count": 100,
        "sector_weights": [
            {"sector": "Unknown", "weight": unknown},
            {"sector": "Technology", "weight": round(1.0 - unknown, 6)},
        ],
        "country_weights": [{"country": "United States", "country_code": "US", "weight": 1.0}],
        "asset_class_weights": [{"asset_class": "Equity", "weight": 1.0}],
    }


def test_coverage_reports_the_unknown_share_of_a_written_record(caplog):
    record = _etf("SPY", unknown=0.3)
    with caplog.at_level(logging.INFO):
        covered = build.report_etf_coverage([{"ticker": "SPY"}], [record], [record], [])
    assert covered == 1
    assert [r for r in caplog.records if "sector 30%" in r.getMessage()], caplog.text


def test_coverage_reports_an_absent_weighted_list_as_absent(caplog):
    record = _etf("SPY")
    del record["sector_weights"]
    with caplog.at_level(logging.INFO):
        build.report_etf_coverage([{"ticker": "SPY"}], [record], [record], [])
    assert [r for r in caplog.records if "sector absent" in r.getMessage()], caplog.text


def test_coverage_names_an_entry_whose_source_failed(caplog):
    with caplog.at_level(logging.WARNING):
        covered = build.report_etf_coverage(
            [{"ticker": "VTI"}], [], [], [("VTI", "NotFoundError: no N-PORT filings")]
        )
    assert covered == 0
    assert [r for r in caplog.records if "VTI" in r.getMessage() and "NotFoundError" in r.getMessage()]


def test_coverage_names_an_entry_whose_record_did_not_validate(caplog):
    """Normalized but rejected by the gate: `write_records` counted it as
    invalid without saying which fund it was."""
    record = _etf("QQQ")
    with caplog.at_level(logging.WARNING):
        build.report_etf_coverage([{"ticker": "QQQ"}], [record], [], [])
    assert [r for r in caplog.records if "QQQ" in r.getMessage() and "did not validate" in r.getMessage()]


def test_coverage_names_an_entry_that_vanished_without_an_error(caplog):
    with caplog.at_level(logging.WARNING):
        build.report_etf_coverage([{"ticker": "IVV"}], [], [], [])
    assert [r for r in caplog.records if "IVV" in r.getMessage() and "no error reported" in r.getMessage()]


def test_coverage_names_a_universe_entry_with_no_ticker(caplog):
    with caplog.at_level(logging.WARNING):
        covered = build.report_etf_coverage([{"cik": "0000884394"}], [], [], [])
    assert covered == 0
    assert [r for r in caplog.records if "no ticker" in r.getMessage()], caplog.text


# ---- the SEC contact guard ----------------------------------------------
#
# `sources.edgar` turns a failed fetch into an empty ticker mapping by design,
# so without an up-front check a missing SEC contact address resolves no CIK,
# writes no ETF record, reaps the 49 already on disk, and still exits 0 --
# publishing a stocks-only dataset that validates.


def test_the_build_refuses_to_start_without_a_sec_contact(tmp_path, monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    monkeypatch.delenv("USER_AGENT", raising=False)
    assert build.main(["--out", str(tmp_path)]) == 2
    assert list(tmp_path.rglob("*.json")) == []


def test_the_guard_does_not_block_a_stocks_only_build(tmp_path, monkeypatch):
    """`--no-etfs` needs no SEC contact, so requiring one would be wrong.

    Stops at the fetch rather than the guard, which is the distinction under
    test: a different failure means the guard let it through.
    """
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    monkeypatch.delenv("USER_AGENT", raising=False)

    def no_network(*a, **kw):
        raise AssertionError("reached the fetch, so the guard did not block")

    monkeypatch.setattr(build.finance_database, "fetch_equities", no_network)
    with pytest.raises(AssertionError, match="guard did not block"):
        build.main(["--no-etfs", "--out", str(tmp_path)])
