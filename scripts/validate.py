"""Validate generated dataset against JSON Schema + custom invariants.

CLI:
    python scripts/validate.py v1/

Also exposed as a Python API:
    from validate import validate_record, validate_tree, shard_paths, ValidationError
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import jsonschema
from jsonschema import Draft202012Validator

import normalize

log = logging.getLogger(__name__)

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
SCHEMA_DIR = REPO_ROOT / "schema"

WEIGHT_SUM_TOL = 0.005


class ValidationError(Exception):
    pass


# ---- schema loaders -----------------------------------------------------

_validators: dict[str, Draft202012Validator] = {}


def _validator(name: str) -> Draft202012Validator:
    if name not in _validators:
        path = SCHEMA_DIR / f"{name}.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        _validators[name] = Draft202012Validator(schema)
    return _validators[name]


def _schema_name_for(record: dict) -> str:
    kind = record.get("kind")
    if kind not in {"stock", "etf"}:
        raise ValidationError(f"unknown kind: {kind!r}")
    return kind


# ---- public API ---------------------------------------------------------


def shard_paths(directory: Path) -> list[Path]:
    """Every shard under `directory`, including any that a path separator nested.

    A shard key containing `/` -- FinanceDatabase publishes share classes as
    `BRK/A` -- makes `build.py` create a directory, so a one-level glob leaves
    those records unvalidated, unindexed, and unreaped. Sorted, because two
    callers print a report and two write a generated artifact that should not
    depend on filesystem enumeration order.
    """
    if not directory.exists():
        return []
    return sorted(directory.rglob("*.json"))


def validate_record(record: dict) -> list[str]:
    """Validate a single record. Returns list of error messages (empty = OK)."""
    errors: list[str] = []
    name = _schema_name_for(record)
    v = _validator(name)
    for e in v.iter_errors(record):
        loc = "/".join(str(p) for p in e.absolute_path)
        errors.append(f"schema: {loc}: {e.message}")

    # Custom invariants
    for field in ("sector_weights", "country_weights", "asset_class_weights"):
        ws = record.get(field) or []
        if not ws:
            continue
        total = sum(w.get("weight", 0.0) for w in ws)
        if abs(total - 1.0) > WEIGHT_SUM_TOL:
            errors.append(f"weights: {field} sums to {total:.4f}, expected 1.0 +/- {WEIGHT_SUM_TOL}")

    # The schema checks a code's shape, not its existence, so `XX` -- what an
    # N-PORT filer writes for a holding it does not place -- reaches a record
    # looking valid. A client resolves the code to a country, and one that ISO
    # 3166-1 never assigned is worse than an absent one.
    for label, code in _country_codes(record):
        if normalize.alpha2_to_country_name(code) is None:
            errors.append(f"country: {label}: {code!r} is not an assigned ISO 3166-1 alpha-2 code")

    th = record.get("top_holdings") or []
    if th:
        top_total = sum(h.get("weight", 0.0) for h in th)
        if top_total > 1.0 + WEIGHT_SUM_TOL:
            errors.append(f"weights: top_holdings sums to {top_total:.4f}, must be <= 1.0")

    return errors


def _country_codes(record: dict) -> list[tuple[str, str]]:
    """Every country code a record publishes, labelled by where it sits."""
    found = []
    code = record.get("country_code")
    if code:
        found.append(("country_code", code))
    for i, w in enumerate(record.get("country_weights") or []):
        code = w.get("country_code")
        if code:
            found.append((f"country_weights/{i}/country_code", code))
    return found


def validate_index(index: dict, root: Path) -> list[str]:
    errors: list[str] = []
    v = _validator("index")
    for e in v.iter_errors(index):
        loc = "/".join(str(p) for p in e.absolute_path)
        errors.append(f"index: {loc}: {e.message}")

    named: set[str] = set()
    for sym, entry in index.get("symbols", {}).items():
        named.add(entry["path"])
        if not (root / entry["path"]).exists():
            errors.append(f"index: symbol {sym!r} -> {entry['path']} (file missing)")

    for isin, path_str in index.get("isins", {}).items():
        named.add(path_str)
        if not (root / path_str).exists():
            errors.append(f"index: isin {isin} -> {path_str} (file missing)")

    # A client resolves through the index and never guesses a filename, so a
    # shard the index does not name cannot be read by anything.
    counts = index.get("counts", {})
    for kind in ("stocks", "etfs"):
        on_disk = {p.relative_to(root).as_posix() for p in shard_paths(root / kind)}
        kind_named = {p for p in named if p.startswith(f"{kind}/")}
        for path_str in sorted(on_disk - kind_named):
            errors.append(f"index: {path_str} on disk but not named by the index")
        claimed = counts.get(kind)
        if not (claimed == len(on_disk) == len(kind_named)):
            errors.append(
                f"index: counts.{kind}={claimed} but {len(on_disk)} file(s) on disk "
                f"and {len(kind_named)} path(s) named"
            )

    return errors


def validate_shard_names(root: Path) -> list[str]:
    """Shard filenames must be creatable on every platform clients clone to.

    Windows resolves `CON.DE.json` to the console device, which fails checkout
    of the whole repository rather than just that record. Share-class symbols
    nest (`BRK/A`), so every path component is checked. `normalize.shard_key`
    escapes these, so a hit here means a record reached disk without it.
    """
    errors = []
    for kind in ("stocks", "etfs"):
        for path in shard_paths(root / kind):
            rel = path.relative_to(root / kind)
            for part in rel.parts:
                if part.partition(".")[0].upper() in normalize.RESERVED_DEVICE_NAMES:
                    errors.append(
                        f"names: {kind}/{rel.as_posix()}: {part!r} is a reserved device name"
                    )
                    break
    return errors


def validate_tree(root: Path) -> int:
    """Validate every file in `root`. Returns count of errors."""
    total_errors = 0

    for kind in ("stocks", "etfs"):
        for path in shard_paths(root / kind):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"FAIL {path}: invalid JSON: {e}")
                total_errors += 1
                continue
            errs = validate_record(record)
            for err in errs:
                print(f"FAIL {path}: {err}")
            total_errors += len(errs)

    errs = validate_shard_names(root)
    for err in errs:
        print(f"FAIL {root}: {err}")
    total_errors += len(errs)

    index_path = root / "index.json"
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"FAIL {index_path}: invalid JSON: {e}")
            return total_errors + 1
        errs = validate_index(index, root)
        for err in errs:
            print(f"FAIL {index_path}: {err}")
        total_errors += len(errs)
    else:
        print(f"FAIL: {index_path} missing")
        total_errors += 1

    return total_errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate.py <root-dir>", file=sys.stderr)
        return 2
    root = Path(argv[1])
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    errors = validate_tree(root)
    if errors:
        print(f"\n{errors} error(s)")
        return 1
    print(f"OK: {root}")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sys.exit(main(sys.argv))
