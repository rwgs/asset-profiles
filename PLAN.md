# Stop a path separator in a shard key creating an unreachable shard

Approach for the change currently in flight: `TASKS.md` **T6**. Replaced when
the next non-trivial change begins, so anything that must outlive this change is
promoted first: decisions that constrain future work to `DECISIONS.md`, and
verified facts that change how the project is understood to `AGENTS.md` or
`SPEC.md`.

**This change sits on top of
[PR #5](https://github.com/wealthfolio/asset-profiles/pull/5), which is open and
unmerged.** #5 fixes the other half of the same function: a
key component colliding with a DOS device name. It deliberately leaves the
separator alone, splitting a key on `/` and escaping each component so `BRK/A`
stays nested by design. Do not start this before #5 merges, or the two rewrite
`shard_key` against each other.

## Problem

`normalize.shard_key` (`scripts/normalize.py:218`) returns an upstream
identifier verbatim, and `build.py` interpolates it straight into a path at
four places: the two index paths (`build.py:208`, `build.py:219`) and the two
written filenames (`build.py:289`, `build.py:323`). There,
`path.parent.mkdir(parents=True, exist_ok=True)` (`build.py:84`) creates
whatever directories the result implies.

**A key containing a path separator becomes a directory.** FinanceDatabase
publishes share classes as `BRK/A`, so `v1/stocks/BRK/A.json` is written instead
of one file. Nine such directories exist, holding 13 records. Because
`build_index` (`build.py:334`), `reap_removed` (`build.py:91`), and
`validate_tree` (`validate.py:117`) all glob `*.json` one level deep, these 13
records are absent from `index.json`, never schema-validated, and never reaped.
They are committed to git. No client can reach them and no check can see them.

The neighbouring defect -- a key matching a DOS device name, which makes the
repository refuse to clone on Windows at all -- is #5's, not this change's. What
#5 leaves behind is the separator: it escapes device names *per component*, so a
future `CON/A` cannot create a reserved directory, and `BRK/A` still nests.

Current behavior is silence. Nothing logs, nothing fails, and the data looks
fine from Linux. #5's new `validate_shard_names` walks the tree with `rglob`, so
it is the first check that even sees a nested path, but it inspects the name for
device collisions and does not validate the record.

## Constraints discovered

Each measured against this working tree on 2026-09-02, not inferred.

- **`-` is not available as an escape character.** Eleven of the 13 nested keys
  already have a correct dash-form shard on disk: `BRK-A`, `AKO-A`, `AKO-B`,
  `BF-A`, `BF-B`, `BRK-B`, `CRD-A`, `CRD-B`, `HEI-A`, `HVT-A`, `WSO-B`. Mapping
  `/` to `-` would manufacture the exact collision this change exists to detect.
  Only `BIO/B` and `RAC/WS` have no dash-form equivalent.
- **`_` is free, and #5 already claims it.** Zero of the 98,462 flat shard stems
  contain `_`, and zero end in `_`; verified by scanning every stem. #5 uses `_`
  as its device-name escape for exactly that reason, so reusing it here gives
  the dataset one escape convention rather than two. The outputs cannot
  collide: #5 emits `_` only directly after a device-name head, so `CON/A`
  becomes `CON_/A` then `CON__A`, which no upstream key can produce.
- **`%` is free too** (zero stems contain it), but percent-encoding is the worse
  choice: these keys become URL path segments on a CDN, and `%2F` in a path is
  normalized back to `/` by enough intermediaries to make the encoded form
  unreliable in exactly the case it is meant to fix.
- **No existing stem's first dot-segment is a reserved device name**, because
  the two that would be cannot exist in this Windows tree. On Linux there are
  two. So the reserved-name rule must be applied by matching the segment before
  the first dot, not the whole stem.
- **`BRK/A` and `BRK-A` are two upstream rows for the same security**, not two
  securities. Same name, sector, country, and market-cap band; the `/` row is
  missing `industry` and `website` and carries a different summary. Neither
  carries an ISIN, so `group_cross_listings` -- which merges only by ISIN --
  cannot combine them. Eleven of the 13 nested records are therefore duplicates
  of a record that already publishes correctly.
- **`apply_overrides` (`normalize.py:462`) resolves an override file by shard
  key**, so any change to the key changes the filename a contributor must use.
  `manual_overrides/` currently holds only its README, so nothing breaks today,
  but `manual_overrides/README.md` documents the naming rule and must be updated
  in step.

## Approach

Extend #5's `shard_key` rather than adding a second sanitiser beside it.

#5 already made `shard_key` filesystem-aware and documented it as such:

```python
key = record.get("isin") or record["primary_symbol"]
return "/".join(_escape_device_name(part) for part in key.split("/"))
```

The `"/".join(...)` is the line to change. Replace the separator with `_` after
escaping each component, so the function returns a single filename component:
`BRK/A` becomes `BRK_A`, and `CON/A` becomes `CON__A`.

Escaping only what the filesystem refuses is the point. Every one of the 98,462
well-formed keys must come out byte-identical, or the change invalidates every
cached client path for no reason. That holds here because no upstream key
contains `_`.

Detect collisions where the keys are collected. `stock_keys` and `etf_keys`
(`build.py:288`, `build.py:322`) are already sets, so a key present before
insertion is a collision: log it as an error against both records and skip the
second, rather than letting `write_if_changed` overwrite. This is the check that
matters most here, because escaping is what can create a collision.

Update `manual_overrides/README.md` and `CONTRIBUTING.md`, both of which #5
already touches to document the device-name rule, to state the separator rule in
the same place.

The build's own re-read and reap globs stay as they are. They are T4's scope,
and once no key produces a directory there is nothing nested left for them to
miss.

## Trade-offs

**`BRK_A` and `BRK-A` will both publish, as separate records for one security.**
This change makes the duplicate visible and addressable instead of hidden in a
directory; it does not resolve it. Resolving it means either dropping the
`/`-form rows or normalizing the symbol separator upstream and merging, and both
settle a data question about what the dataset publishes. Per `AGENTS.md` that
needs asking, not implementing, so it is raised separately rather than folded in
here.

**Rejected: map `/` to `-`.** The obvious scheme, and wrong -- it collides with
11 existing shards, as measured above.

**Rejected: percent-encode.** Reversible and unambiguous on disk, unreliable as
a CDN path segment.

**Rejected: drop any record whose key needs escaping.** Smallest possible
change, and it silently loses `BIO/B` and `RAC/WS`, which have no alternate
form. Dropping data to avoid escaping it is the wrong trade at 13 records and a
worse one at scale.

**Reversed: keeping `shard_key` purely logical.** This plan originally proposed
a separate `fs_safe_key`, leaving `shard_key` free of filesystem concerns, on
the grounds that override lookup and logging should not inherit one. #5 settles
it the other way and is the better call: an override filename has to match the
file on disk, so a `shard_key` that does not is a trap for contributors, which
is why #5 updates `manual_overrides/README.md` in the same PR.

**Risk that survives:** the escaped forms are new paths, so a client holding a
cached `index.json` will keep asking for `stocks/BRK/A.json` until its index TTL
expires. That URL 404s rather than misresolving, and the spec already requires a
client to treat a miss as normal, so the failure mode is a brief coverage gap
for 13 records nothing can currently read anyway.

## Verification

**Automated**, in the `pytest` harness under `scripts/tests/`:

- `shard_key` over each observed separator key -- `BRK/A`, `BF/A`, `AKO/B`,
  `RAC/WS`, `BIO/B` -- asserting the exact expected output contains no `/`.
  These five already exist as `xfail(strict=True)`, asserting only the absence
  of a separator, so this change tightens them to the expected key and drops
  the marker.
- `shard_key` over `CON`, `CON.DE`, and `CON/A`, asserting #5's device escaping
  still applies and composes with this one: `CON_`, `CON_.DE`, `CON__A`.
  Catches a change that replaces #5's rule instead of extending it, which is
  the regression this plan's ordering exists to prevent.
- A regression case asserting `US0378331005`, `AAPL`, `BRK-A`, and `VOD.L` are
  returned unchanged. Catches an escaping rule applied too broadly, which is the
  one failure mode that would break working clients.
- Two records escaping to one key, asserting an error is reported and no
  overwrite occurs. Catches the silent-overwrite path.
- A round trip through `validate_record` on a record whose key was escaped,
  asserting the record still validates.

**Manual:**

- `python scripts/build.py --limit 3000 --out ./probe`, then confirm
  `probe/stocks/` contains no directories. Uses a bounded tree so the check is
  readable.
- On Windows, in a plain console: confirm the previously nested records are
  written as flat files and are readable. #5 owns the equivalent check for the
  `CON` shards; neither can be tested on the CI runner.

**Not verifiable in this environment:** the full `v1/` rebuild that produces the
repaired tree. It needs a live EDGAR and FinanceDatabase fetch, and it is a
tens-of-thousands-of-files rewrite that `TASKS.md` T5 holds behind sign-off. A
`--limit` build over a real FinanceDatabase pull is the closest check available
here, and the `.http_cache/` directory in this tree may already hold the CSV it
needs.
