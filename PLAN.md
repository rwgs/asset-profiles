# Make an unreachable or unvalidated shard a validator failure

Approach for the change currently in flight: `TASKS.md` **T4**. Replaced when
the next non-trivial change begins, so anything that must outlive this change is
promoted first: decisions that constrain future work to `DECISIONS.md`, and
verified facts that change how the project is understood to `AGENTS.md` or
`SPEC.md`.

The previous occupant of this file was T6, the shard-key separator fix, which is
blocked on [PR #5](https://github.com/wealthfolio/asset-profiles/pull/5) and
cannot start until it merges. Its durable part -- the escape character and the
measurement that rules out the obvious alternative -- is now a `DECISIONS.md`
entry dated 2026-09-02, and `TASKS.md` T6 points there.

**Base this on T3, not on `upstream/main`.** T4 rewrites the exact lines T3
changed: `validate.py` 120 and 133 are inside the two read loops this change
merges into one walk, and `build.py` 335 and 339 are the re-read named below. A
branch cut off `upstream/main` writes the new walk against the unfixed base and
silently drops `encoding=` back out.

## Problem

The gate cannot see part of the tree it is meant to gate, and the index cannot
name part of the tree it is meant to index. Three quantities that must be equal
are all different, and the validator checks only one of the pairs.

Measured 2026-09-02 against this working tree at `2a76205957`:

| Quantity | Stocks | ETFs |
| --- | --- | --- |
| `counts.stocks` / `counts.etfs` in `index.json` | 98,464 | 10 |
| Distinct paths the index names, via `symbols` and `isins` | 98,463 | 10 |
| `.json` files directly under the directory | 98,462 | 10 |
| `.json` files one level down | 13 | 0 |

The flat figure is 98,462 rather than 98,464 because this is a Windows tree and
the two `CON` shards cannot exist on it -- PR #5's defect, not this one's. On
Linux it reads 98,464, which is where the three-way disagreement is clearest:
98,464 records counted, 98,463 reachable, 98,477 on disk.

Three causes, all of them silence:

- **`validate_tree` (`validate.py:117`, `validate.py:130`) globs `*.json` one
  level deep**, twice, once per kind. The 13 records in the nine directories
  under `v1/stocks/` are never schema-validated. They pass -- verified by
  running `validate_record` over all 13 -- so the cost today is a check that
  does not run rather than an error that is hidden, and that is luck rather
  than design.
- **`validate_index` checks only one direction.** It confirms every path the
  index names exists on disk, and never that every file on disk is named. So a
  shard nothing can reach is not a failure.
- **`counts` is reconciled against the same one-level glob**
  (`validate.py:102`), so it agrees with neither the tree nor the index.

**The gap of one is identified.** `stocks/SAND.json` is a flat, schema-valid,
unreachable record: a Sandstorm Gold row carrying no ISIN, whose only listing
symbol is `SAND`. The same security also appears as `stocks/CA80013R2063.json`,
an ISIN-bearing record that merged seven cross-listings and lists `SAND` among
them. Both records are written; `build_index` writes `symbols["SAND"]` twice and
the last writer wins, which on the run that produced this tree was the ISIN one.
So one record on disk contributes no path to the index at all, which is exactly
the missing one. `group_cross_listings` merges only by ISIN, so the ISIN-less
duplicate cannot be absorbed -- the same root cause as `BRK/A` beside `BRK-A`.

The build has the matching blind spots: `reap_removed` (`build.py:89`) and the
re-read that feeds `build_index` (`build.py:335`, `build.py:339`) glob one level
too, so a nested record is never reaped and never reaches the index.

## Constraints discovered

- **All 13 nested records and `SAND.json` pass `validate_record`.** So the new
  schema pass over them adds no failures, and every new error this change
  reports comes from the reachability check. That makes the change's effect on
  the gate exactly measurable in advance: 14 orphan errors plus one
  reconciliation error.
- **`index.schema.json` already permits a nested path.** Its pattern is
  `^(stocks|etfs)/.+\.json$`, and `.` matches `/`. So indexing the nested
  records is schema-legal, and the schema is not what has been keeping them out.
- **None of the 13 nested records' symbols is in the index today.** Each lists
  exactly one symbol, the slash form (`BRK/A`), and none of those keys appears
  in `symbols`. So making the re-read recursive adds 13 symbol keys and steals
  none: `BRK-A` is a different key from `BRK/A`.
- **A second walk is affordable.** `rglob("*.json")` over `v1/stocks/` costs
  0.57s against 0.50s for `glob`, on a run that takes 82 seconds. So
  `validate_index` can do its own walk and keep its `(index, root)` signature
  rather than having results threaded in from `validate_tree`.

## Approach

One walk helper in `validate.py`, used at all four sites.

```python
def shard_paths(directory: Path) -> list[Path]:
    """Every shard under `directory`, including any that a path separator nested."""
```

Sorted, because two of the callers want a readable report and the other two
write a generated artifact whose contents should not depend on filesystem
enumeration order.

- **`validate_tree`** loops `for kind in ("stocks", "etfs")` over that helper,
  which collapses its two duplicated bodies into one. Nested records get
  schema-validated.
- **`validate_index`** accumulates the paths it already reads from `symbols` and
  `isins` into a set, then per kind reports every file on disk that set does not
  name, and replaces the `counts` check with a three-way one: the claimed count,
  the files on disk, and the distinct paths named must all agree, and the
  message prints all three so a reader can see which two do.
- **`build.reap_removed`** walks recursively and compares the path relative to
  the directory, minus `.json`, against the key set -- not `path.stem`, which
  for `BRK/A.json` is `A` and matches no key, so a recursive reap keyed on the
  stem would delete every nested record on the next build. The relative form is
  the shard key by construction.
- **The re-read feeding `build_index`** uses the same helper, so a record on
  disk is a record in the index and the reconciliation above can hold for a
  freshly built tree.

## Trade-offs

**This turns the gate red on the committed data, and that is the decision the
change asks for.** `python scripts/validate.py v1/` goes from 0 errors to 15 on
Linux: 14 shards on disk that the index does not name, plus one line reporting
that 98,464 counted, 98,477 on disk, and 98,463 named are three different
numbers. On Windows it reads 17, the three pre-existing `CON` failures included.
Green returns when T6 repairs the keys and T5 rebuilds -- or sooner, by deleting
the 14 orphans, which is 14 files rather than T5's 98,000 and is sign-off work
either way. Reporting a defect that already exists is the point of a gate; the
alternative is a check that passes because it is not looking.

**The re-read becomes sorted, so an index tie-break stops depending on the
filesystem.** Two records claiming one symbol -- `SAND` today -- resolve by
whichever is written last, which was previously directory enumeration order and
is now alphabetical. On the next rebuild `symbols["SAND"]` therefore flips from
the ISIN-bearing record to the ISIN-less one, because `CA80013R2063.json` sorts
before `SAND.json`. That is a worse record winning a symbol, and it is visible
rather than arbitrary. Fixing it means resolving the duplicate, which settles a
data question and is raised rather than folded in.

**A duplicate claim is only sometimes detectable.** `symbols` is a JSON object,
so one record overwriting another's symbol leaves no trace in the output; the
only observable is a record that contributes no path at all, which is what
catches `SAND` today. After a rebuild, sorted order gives `SAND.json` the symbol
and leaves `CA80013R2063.json` reachable through `isins`, so all three
quantities agree and the duplicate stops being reported. The check is a
reachability check, not a de-duplication check, and this plan does not pretend
otherwise.

**Rejected: thread `validate_tree`'s walk into `validate_index`.** Saves 0.6s
of a 82s run and changes a signature the tests call directly, to remove a cost
that was measured and is not there.

**Rejected: make the orphan report a warning.** It would keep CI green, and a
gate that warns is not a gate. The three `CON` failures on Windows were the
symptom that got PR #5 written; a warning would have been ignored for the same
three months.

**Rejected: fold the 14 deletions in.** It keeps the gate green, and per
`AGENTS.md` deleting tracked data is not implied by a request to fix the check
that finds it. T5 owns it, behind sign-off.

**Rejected: remove a directory `reap_removed` empties.** Once T6 lands, the nine
nested directories are reaped to empty and stay on disk. Git does not track an
empty directory, so nothing reaches the published tree, and adding directory
removal to a function that deletes files is a widening of what it may destroy
for no observable gain.

## Verification

**Automated**, in `scripts/tests/test_validate.py`:

- A flat shard on disk that the index does not name is an error naming that
  path. Red before the change, since nothing checked the direction.
- A nested shard on disk that the index does not name is the same error. Red
  before, since nothing saw the file.
- A nested shard whose record is invalid is reported by `validate_tree`, on a
  fixture whose index names it and whose counts agree, so the schema error is
  the only one. `validate_tree` returned 0 for this tree before the change.
- A count matching neither the disk nor the index reports all three numbers.
- The existing well-formed one-shard tree still returns 0, which is what proves
  the reconciliation does not fire on a correct tree. Already asserted by
  `test_a_record_the_host_locale_cannot_decode_still_validates`.

`conftest.py`'s `index_of` fixture gains an `also` argument naming extra shard
paths, keyed in `symbols` by the shard key the path implies, which is what
`build_index` does.

**Manual:**

- `python scripts/validate.py v1/` before and after, comparing the error count
  against the 15 and 17 predicted above. This is the check that the measurement
  in this plan is right, not just that the code runs.
- `python scripts/build.py --no-stocks --no-etfs --out <dir>` over a fixture
  tree holding a nested shard: both fetch passes are skipped, so it reaches
  nothing but `reap_removed` and the re-read, with no network. Confirms the
  nested record reaches `index.json` and is not reaped. This is how T3 verified
  the same two lines.

**Not covered, and disclosed rather than papered over:** `reap_removed` and the
re-read have no automated test. A test for either has to `import build`, which
pulls in `pandas`, `requests`, and `lxml`, and `AGENTS.md` records that the
suite runs with only `pycountry` and `jsonschema` installed -- which is what
makes it runnable on a host where the full requirements do not install (T8). The
walk itself is covered, at the three validator sites; its two build call sites
are covered by the manual probe above. Trading the suite's independence from the
heavy dependencies for coverage of two lines is the wrong way round, but it is a
gap and it is T8's resolution that closes it properly.
