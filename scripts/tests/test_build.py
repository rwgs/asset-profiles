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
