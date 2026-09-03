"""Asset Profiles build pipeline.

Produces:
  v1/index.json
  v1/stocks/{ISIN-or-symbol}.json
  v1/etfs/{ISIN-or-symbol}.json

Idempotency: only rewrites a shard file if its SHA256 changed; index.json
is always rewritten because timestamps tick.

Usage:
  SEC_USER_AGENT="name email" python scripts/build.py [--no-etfs] [--limit N]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Iterable

import yaml

# Allow `from sources.foo import bar` when run as `python scripts/build.py`.
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from sources import finance_database  # noqa: E402
from sources import edgar  # noqa: E402
from sources import issuer_scraper  # noqa: E402
from sources import openfigi  # noqa: E402

import http_cache  # noqa: E402
import normalize  # noqa: E402
import validate as validate_mod  # noqa: E402

log = logging.getLogger("build")

REPO_ROOT = SCRIPTS_DIR.parent
CONFIG_DIR = REPO_ROOT / "config"
OVERRIDES_DIR = REPO_ROOT / "manual_overrides"
OUT_DIR = REPO_ROOT / "v1"
SCHEMA_VERSION = "1.0.0"


# ---- helpers ------------------------------------------------------------


def utcnow_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def add_days(iso: str, days: int) -> str:
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (t + dt.timedelta(days=days)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_mappings() -> dict:
    return {
        "exchange_mic": load_yaml(CONFIG_DIR / "exchange_mic.yml"),
        **load_yaml(CONFIG_DIR / "sector_taxonomy.yml"),
    }


def write_if_changed(path: Path, payload: dict, *, summary: dict) -> None:
    """Write `path` only if its serialized form differs from current contents."""
    body = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    new_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if path.exists():
        old_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if old_hash == new_hash:
            summary["unchanged"] += 1
            return
        summary["changed"] += 1
    else:
        summary["added"] += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def reap_removed(directory: Path, current_keys: set[str], summary: dict) -> None:
    for path in validate_mod.shard_paths(directory):
        # A nested shard's key is its path below `directory`, not its stem:
        # `BRK/A.json` is keyed `BRK/A` and stemmed `A`, so reaping on the stem
        # would delete every record a path separator nested.
        if path.relative_to(directory).with_suffix("").as_posix() not in current_keys:
            path.unlink()
            summary["removed"] += 1


def write_records(
    records: Iterable[dict], directory: Path, kind: str, *, summary: dict
) -> tuple[set[str], int]:
    """Override, validate, and write each record as one shard, then reap.

    Returns the keys written and the number of records that were not, so the
    caller can report both. A key already written is a collision: report it and
    skip, rather than letting the second record silently replace the first.
    """
    keys: set[str] = set()
    invalid = 0
    for record in records:
        record = normalize.apply_overrides(record, OVERRIDES_DIR)
        errs = validate_mod.validate_record(record)
        if errs:
            invalid += 1
            for e in errs[:3]:
                log.warning("%s %s: %s", kind, normalize.shard_key(record), e)
            continue
        key = normalize.shard_key(record)
        if key in keys:
            log.error(
                "%s %s: shard key %r is already written; skipping this record",
                kind, record.get("primary_symbol"), key,
            )
            invalid += 1
            continue
        keys.add(key)
        write_if_changed(directory / f"{key}.json", record, summary=summary)
    reap_removed(directory, keys, summary)
    return keys, invalid


# ---- stocks pass --------------------------------------------------------


def build_stocks(mappings: dict, fetched_at: str, limit: int | None = None) -> list[dict]:
    iterator = finance_database.fetch_equities()
    normalized = []
    seen = 0
    for row in iterator:
        seen += 1
        rec = normalize.normalize_stock(row, fetched_at=fetched_at, mappings=mappings)
        if rec is not None:
            normalized.append(rec)
            if limit and len(normalized) >= limit:
                break
    log.info("normalized %d stock records (from %d input rows)", len(normalized), seen)
    grouped = normalize.group_cross_listings(normalized)
    log.info("after cross-listing merge: %d records", len(grouped))
    apply_figi_identity(grouped)
    return grouped


def figi_identity(
    records: list[dict], figi_by_isin: dict[str, list[dict]]
) -> tuple[dict[str, str], set[str]]:
    """Split an OpenFIGI sweep into a type per ISIN and the ISINs to disown.

    An ISIN is disowned only on two independent signals: OpenFIGI names a
    different company, *and* the ISIN's country prefix is an assigned ISO
    country that disagrees with the record's own `country_code`. One signal
    alone is not enough. A rename or a transliteration trips the name check
    while staying in its own country -- `Orocobre Limited` is now
    `ALLKEM LTD` -- and the offshore-domicile class trips the country check
    while being perfectly correct. Measured 2026-09-03 over the published
    tree: the name check alone fires on 888 records, the country check alone
    on 1,927, and 322 fail both.

    The prefix has to be a real country for the second signal to mean
    anything. A Eurobond is `XS`, which claims no jurisdiction, so comparing
    it against a record's `country_code` would fire on every one of them.

    Disowning is checked before typing, and not the other way round. A wrong
    ISIN can point at a fund as easily as at a share -- `LU0950674332` is a
    Luxembourg fund and the record wearing it is SeaChange International, a
    US software company -- and typing first would republish SeaChange as a
    fund instead of taking the bad identifier off it. Ordering it this way
    also still spares the 478 notes and structured certificates, whose names
    differ from their issuer's legitimately (`EGB OE TL.Z./ZALANDO` is issued
    by `ERSTE GROUP BANK AG`) but whose ISINs are Austrian exactly like the
    records carrying them, so the country signal never fires.
    """
    kind_by_isin: dict[str, str] = {}
    wrong_isins: set[str] = set()

    for record in records:
        isin = record.get("isin")
        data = figi_by_isin.get(isin) if isin else None
        if not data:
            continue

        names = openfigi.security_names(data)
        country_code = record.get("country_code")
        prefix = isin[:2]
        prefix_disagrees = (
            bool(country_code)
            and prefix != country_code
            and normalize.alpha2_to_country_name(prefix) is not None
        )
        if prefix_disagrees and openfigi.names_disagree(record.get("name") or "", names):
            wrong_isins.add(isin)
            log.info(
                "%s names %r; OpenFIGI names %r -- dropping the ISIN",
                isin, record.get("name"), names[:3],
            )
            continue

        kind_by_isin[isin] = openfigi.security_kind(data)

    return kind_by_isin, wrong_isins


def apply_figi_identity(records: list[dict]) -> None:
    """Type non-equities and disown wrong ISINs, in place.

    A failure here leaves every record exactly as the source reported it and
    the build continues, because this corrects published metadata rather than
    supplying any: OpenFIGI being down should not empty the dataset. That is
    the same posture `issuer_scraper` gets, and the reason the count reaches
    the log either way.
    """
    isins = [r["isin"] for r in records if r.get("isin")]
    if not isins:
        return
    try:
        figi_by_isin = openfigi.map_isins(isins)
    except openfigi.CredentialError:
        # A rejected key is the operator's to fix and fails every batch, so
        # degrading here would publish the very defects this corrects and
        # still exit 0. `main` turns it into exit 2.
        raise
    except Exception:
        log.warning("OpenFIGI sweep failed; publishing source types unchanged", exc_info=True)
        return

    kind_by_isin, wrong_isins = figi_identity(records, figi_by_isin)
    summary = normalize.apply_instrument_identity(
        records, kind_by_isin=kind_by_isin, wrong_isins=wrong_isins
    )
    log.info(
        "OpenFIGI: typed %d of %d ISINs; retyped %d record(s) (%d lost an inherited "
        "sector), dropped %d ISIN(s) naming another company",
        len(figi_by_isin), len(isins), summary["retyped"],
        summary["sector_dropped"], summary["isin_dropped"],
    )


# ---- ETFs pass ----------------------------------------------------------


def _index_stocks(stocks: Iterable[dict]) -> tuple[dict, dict, dict]:
    """Index the stocks pass by every identifier a holding might carry."""
    by_isin: dict[str, dict] = {}
    by_symbol: dict[str, dict] = {}
    by_cusip: dict[str, dict] = {}
    for s in stocks:
        if s.get("isin"):
            by_isin[s["isin"]] = s
        for lst in s.get("listings", []):
            by_symbol[lst["symbol"]] = s
        cusip = (s.get("identifiers") or {}).get("cusip")
        if cusip:
            by_cusip[cusip] = s
    return by_isin, by_symbol, by_cusip


def build_etfs(
    universe: list[dict],
    fd_etfs_meta: dict[str, dict],
    stocks_by_isin: dict[str, dict],
    stocks_by_symbol: dict[str, dict],
    stocks_by_cusip: dict[str, dict],
    fetched_at: str,
    mappings: dict,
) -> tuple[list[dict], list[tuple[str, str]]]:
    """Returns (etf_records, errors). One failed ETF doesn't abort the build."""
    records: list[dict] = []
    errors: list[tuple[str, str]] = []

    for entry in universe:
        ticker = entry.get("ticker")
        if not ticker:
            continue
        meta_extra = dict(fd_etfs_meta.get(ticker, {}))
        meta_extra.update(entry)  # universe-level overrides win
        meta_extra.setdefault("symbol", ticker)

        cik = entry.get("cik")
        source_label = source_url = license_label = None
        holdings = None

        try:
            if cik:
                holdings = edgar.fetch_latest_nport(cik, ticker=ticker)
                source_label = "SEC EDGAR N-PORT"
                source_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"
                license_label = "public domain"
        except (edgar.NotFoundError, edgar.NotUSDomiciledError) as e:
            log.info("EDGAR miss for %s: %s; falling back to issuer scraper", ticker, e)
            holdings = None
        except Exception as e:
            log.warning("EDGAR error for %s: %s", ticker, e)

        if holdings is None:
            try:
                issuer = entry.get("issuer") or meta_extra.get("issuer")
                holdings = issuer_scraper.fetch_issuer_holdings(ticker, issuer)
                source_label = f"Issuer holdings ({issuer or 'unknown'})"
                source_url = issuer_scraper.source_url_for(ticker, issuer)
                license_label = "issuer ToS (attributed, non-commercial)"
            except Exception as e:
                msg = f"{type(e).__name__}: {e}"
                log.error("ETF %s failed: %s", ticker, msg)
                errors.append((ticker, msg))
                continue

        try:
            record = normalize.normalize_etf(
                meta_extra,
                holdings,
                fetched_at=fetched_at,
                stocks_by_isin=stocks_by_isin,
                stocks_by_symbol=stocks_by_symbol,
                stocks_by_cusip=stocks_by_cusip,
                source_label=source_label,
                source_url=source_url,
                license_label=license_label,
            )
            records.append(record)
        except Exception as e:
            msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            log.error("normalize failed for %s: %s", ticker, e)
            errors.append((ticker, msg))

    return records, errors


# ---- coverage report ----------------------------------------------------


def _unknown_share(record: dict, field: str, key: str, label: str) -> str:
    ws = record.get(field) or []
    if not ws:
        return "absent"
    return f"{sum(w.get('weight', 0.0) for w in ws if w.get(key) == label):.0%}"


def report_etf_coverage(
    universe: list[dict],
    normalized: list[dict],
    written: list[dict],
    errors: list[tuple[str, str]],
) -> int:
    """One line per universe entry: its unknown share, or why it has no record.

    The build reported aggregate counts, under which a universe entry could
    vanish without ever being named and a record whose weights are entirely
    `Unknown` looked the same as one that carries signal. Both are failures.
    Returns the number of entries that produced a record.
    """
    failed = dict(errors)
    normalized_by = {r.get("primary_symbol") for r in normalized}
    written_by = {r.get("primary_symbol"): r for r in written}

    covered = 0
    log.info("ETF coverage, one line per universe entry:")
    for entry in universe:
        ticker = entry.get("ticker")
        if not ticker:
            log.warning("  <no ticker>: universe entry has no ticker key: %r", entry)
            continue
        record = written_by.get(ticker)
        if record is None:
            if ticker in failed:
                reason = failed[ticker].splitlines()[0]
            elif ticker in normalized_by:
                reason = "record built but did not validate"
            else:
                reason = "no holdings found and no error reported"
            log.warning("  %-6s no record: %s", ticker, reason)
            continue
        covered += 1
        log.info(
            "  %-6s %4d holdings, unknown: sector %s, country %s, asset class %s",
            ticker,
            record.get("holdings_count") or 0,
            _unknown_share(record, "sector_weights", "sector", "Unknown"),
            _unknown_share(record, "country_weights", "country", "Unknown"),
            _unknown_share(record, "asset_class_weights", "asset_class", "Other"),
        )
    log.info("ETF coverage: %d of %d universe entries produced a record", covered, len(universe))
    return covered


# ---- index --------------------------------------------------------------


def build_index(stocks: list[dict], etfs: list[dict], generated_at: str) -> dict:
    symbols: dict[str, dict] = {}
    isins: dict[str, str] = {}

    for record in stocks:
        path = f"stocks/{normalize.shard_key(record)}.json"
        for lst in record.get("listings", []):
            symbols[lst["symbol"]] = _strip_none({
                "kind": "stock",
                "path": path,
                "isin": record.get("isin"),
            })
        if record.get("isin"):
            isins[record["isin"]] = path

    for record in etfs:
        path = f"etfs/{normalize.shard_key(record)}.json"
        for lst in record.get("listings", []):
            symbols[lst["symbol"]] = _strip_none({
                "kind": "etf",
                "path": path,
                "isin": record.get("isin"),
            })
        if record.get("isin"):
            isins[record["isin"]] = path

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "next_refresh_at": add_days(generated_at, 7),
        "counts": {
            "stocks": len(stocks),
            "etfs": len(etfs),
        },
        "symbols": symbols,
        "isins": isins,
    }


def _strip_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


# ---- main ---------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-etfs", action="store_true", help="skip ETF pass (stocks only)")
    parser.add_argument("--no-stocks", action="store_true", help="skip stocks pass (ETFs only)")
    parser.add_argument("--limit", type=int, default=None, help="cap number of stocks (debug)")
    parser.add_argument("--out", default=str(OUT_DIR), help="output root (default: v1/)")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "stocks").mkdir(exist_ok=True)
    (out_dir / "etfs").mkdir(exist_ok=True)

    # Before the stocks pass rather than after it. The ETF pass needs a SEC
    # contact address, and `sources.edgar` turns a failed fetch into an empty
    # ticker mapping, so a missing one would resolve no CIK, write no ETF
    # record, reap the ones already on disk, and still exit 0 -- publishing a
    # stocks-only dataset that validates. Five seconds here beats that.
    if not args.no_etfs:
        try:
            http_cache.check_sec_contact()
        except RuntimeError as e:
            log.error("%s", e)
            return 2

    fetched_at = utcnow_iso()
    mappings = load_mappings()
    summary = {"added": 0, "changed": 0, "unchanged": 0, "removed": 0}

    # ---- stocks ----
    stocks: list[dict] = []
    if not args.no_stocks:
        try:
            stocks = build_stocks(mappings, fetched_at, limit=args.limit)
        except openfigi.CredentialError as e:
            log.error("%s", e)
            return 2

        stock_keys, stock_errors = write_records(
            stocks, out_dir / "stocks", "stock", summary=summary
        )
        log.info("stocks: %d valid, %d invalid", len(stock_keys), stock_errors)

    # ---- ETFs ----
    etfs: list[dict] = []
    etf_errors: list[tuple[str, str]] = []
    if not args.no_etfs:
        universe_path = CONFIG_DIR / "etf_universe.yml"
        if universe_path.exists():
            universe_doc = load_yaml(universe_path)
            universe = universe_doc.get("etfs", []) if isinstance(universe_doc, dict) else universe_doc
            log.info("ETF universe: %d entries", len(universe))

            fd_etf_rows = list(finance_database.fetch_etfs_meta())
            fd_etfs_meta = {r["symbol"]: r for r in fd_etf_rows if r.get("symbol")}

            by_isin, by_symbol, by_cusip = _index_stocks(stocks)
            etfs, etf_errors = build_etfs(
                universe, fd_etfs_meta, by_isin, by_symbol, by_cusip, fetched_at, mappings
            )

            etf_keys, invalid = write_records(
                etfs, out_dir / "etfs", "etf", summary=summary
            )
            written = [r for r in etfs if normalize.shard_key(r) in etf_keys]
            report_etf_coverage(universe, etfs, written, etf_errors)
            etfs = written
            log.info("etfs: %d valid, %d invalid, %d errors", len(etf_keys), invalid, len(etf_errors))
        else:
            log.info("no etf_universe.yml; skipping ETF pass")

    # ---- index ----
    # Re-load successful records from disk to ensure index reflects post-validation truth.
    valid_stocks = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in validate_mod.shard_paths(out_dir / "stocks")
    ]
    valid_etfs = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in validate_mod.shard_paths(out_dir / "etfs")
    ]

    index = build_index(valid_stocks, valid_etfs, generated_at=fetched_at)
    (out_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    log.info(
        "index: %d symbols, %d ISINs (%d stocks, %d ETFs)",
        len(index["symbols"]),
        len(index["isins"]),
        index["counts"]["stocks"],
        index["counts"]["etfs"],
    )

    # ---- summary ----
    log.info(
        "diff: +%d / ~%d / -%d (unchanged %d)",
        summary["added"], summary["changed"], summary["removed"], summary["unchanged"],
    )
    if etf_errors:
        log.warning("ETF errors:")
        for ticker, msg in etf_errors:
            log.warning("  %s: %s", ticker, msg.splitlines()[0])

    return 0


if __name__ == "__main__":
    sys.exit(main())
