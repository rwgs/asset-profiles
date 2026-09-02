# Project tasks

The work in flight and the work already validated. A task is one reviewable
outcome: if it cannot be finished and checked in a single pass, it is a phase
and belongs in `ROADMAP.md`.

Every measurement below was taken on 2026-09-02 against this working tree at
`1979d5a8c3`, on Windows with Python 3.13.9. Re-measure rather than trust a
number here once the pipeline has run again.

## Pull requests

Five are open against `wealthfolio/asset-profiles`, all from forks, and they
cover a large part of Phases 1, 2, and 4. Read this before starting anything
below: three of the tasks in this file are already written and waiting.

| PR | What it does | Author | Opened | State |
| --- | --- | --- | --- | --- |
| [#6](https://github.com/wealthfolio/asset-profiles/pull/6) | Resolve N-PORT by fund series, not filer CIK | rwgs | 2026-09-01 | Open, CI never ran |
| [#5](https://github.com/wealthfolio/asset-profiles/pull/5) | Escape DOS device names in shard filenames | rwgs | 2026-09-01 | Open, CI never ran |
| [#3](https://github.com/wealthfolio/asset-profiles/pull/3) | Correct four wrong CIKs in the universe | bjmc | 2026-06-12 | Open, CI never ran |
| [#2](https://github.com/wealthfolio/asset-profiles/pull/2) | Add funds to the universe | bjmc | 2026-06-12 | Open, CI never ran |
| [#1](https://github.com/wealthfolio/asset-profiles/pull/1) | Point FinanceDatabase at its moved URLs | bjmc | 2026-06-12 | Open, CI never ran |

**Nothing has been validated by anything but review.** Every one of the five
reports `no checks reported`, and the two most recent show GitHub run status
`action_required` at 0s duration: `validate-pr.yml` is gated behind maintainer
approval for fork pull requests, so the repository's only automated check has
never executed against any proposed change. Getting that approval is P1 below,
because it is the cheapest thing on this page and it gates the value of
everything else.

**Merge order matters, and GitHub will not warn about it.**

1. **#1 first.** Until it lands every scheduled refresh fails, so no other
   change can be observed in the published data. See P2.
2. **#3 and #2 conflict with each other**, though both report no conflict with
   `main` -- GitHub computes that against the base branch only. #3 edits BND's
   `cik:` value and #2 inserts BNDX on the following line, so
   `git merge-tree pr3 pr2` conflicts in `config/etf_universe.yml`. Whichever
   lands second needs a rebase. Recorded on both PRs.
3. **#6 subsumes #3's findings** without conflicting with it: #6 derives the
   filing CIK from SEC's own mapping, which independently confirms all four of
   #3's corrections and finds fifteen more, for 19 wrong CIKs out of 52
   configured. #6 touches only `scripts/`, so #3 can still land as explicit
   documentation if the maintainers prefer that. Their call, noted on #3.
4. **#5 is independent** of all of the above.

## Current phase

Phase 1, *A dataset that validates everywhere and hides nothing*. Two items are
already submitted and two are maintainer actions, so the code left to write is
smaller than it looks.

- [ ] **P1.** Get `validate-pr.yml` to run on fork pull requests.
  - Scope: a maintainer action, not a code change. Approve the pending workflow
    runs on #1, #2, #3, #5, and #6, and decide whether first-time fork
    contributors should stay gated. Nothing here needs a commit.
  - Acceptance criteria: `gh pr checks` reports a real result, pass or fail, on
    all five open PRs.
  - Automated validation: the workflow itself, once it is allowed to start.
  - Manual validation: none.
  - Dependencies or blockers: needs repository write access on
    `wealthfolio/asset-profiles`. Cannot be done from a fork.
  - Why first: five changes are waiting on a check that has never executed. The
    cost is a button; the cost of not doing it is that every merge decision
    below is made on review alone.

- [ ] **P2.** Land the FinanceDatabase URL fix and restart the refresh.
  - Scope: merge #1, then re-enable the schedule. Two separate causes stopped
    the weekly job and fixing one does not fix the other.
  - Acceptance criteria: a refresh run completes with conclusion `success` and
    commits; `v1/index.json` `generated_at` moves off 2026-05-31.
  - Automated validation: the refresh workflow's own run.
  - Manual validation: fetch `index.json` from jsDelivr and confirm the date
    moved.
  - Dependencies or blockers: merging #1 needs maintainer access; re-enabling a
    schedule does too.
  - Evidence: nine consecutive scheduled runs failed, 2026-06-07 through
    2026-08-02, every one of them in about 30 seconds on
    `requests.exceptions.HTTPError: 404 Client Error: Not Found for url:
    .../FinanceDatabase/main/database/equities.csv`. FinanceDatabase moved to
    per-exchange CSVs with combined archives under `compression/`, which is
    exactly what #1 repoints to. **Then the runs stop entirely** -- nothing
    after 2026-08-02, four missed Sundays. The last push to `main` was
    2026-05-31, and GitHub disables a scheduled workflow after 60 days without
    repository activity, which lands 2026-07-30. So the 404 is why the job
    failed and the inactivity disable is why it no longer runs, and #1 alone
    will not bring it back.

- [ ] **T1.** Add a test harness and run it in CI.
  - Scope: `pytest` in `scripts/requirements.txt`, tests under `scripts/tests/`,
    a `pytest` step in `.github/workflows/validate-pr.yml`. Cover
    `normalize.shard_key`, `_aggregate_weights`, `apply_overrides`, and
    `validate.validate_record` against a fixture record. No production code
    changes in this task.
  - Acceptance criteria: `pytest scripts/tests` passes locally and in CI on a
    fresh clone; a deliberately broken fixture fails it; `AGENTS.md` gains the
    real command in place of its note that none exists.
  - Automated validation: the suite itself, plus a red-then-green check that CI
    actually fails when a test fails.
  - Manual validation: none needed.
  - Dependencies or blockers: none. This is the prerequisite for T2 to T4, which
    are otherwise unprovable.

- [~] **T2.** Escape DOS device names in shard filenames.
  **Submitted as [#5](https://github.com/wealthfolio/asset-profiles/pull/5),
  2026-09-01. Awaiting CI approval (P1) and review.**
  - Scope as submitted: `shard_key` escapes any path component whose part
    before the first dot is a DOS device name (`CON`, `PRN`, `AUX`, `NUL`,
    `COM0`-`COM9`, `LPT0`-`LPT9`) by appending `_` to that part, so `CON.DE`
    becomes `CON_.DE`. A new `validate_shard_names` walks the tree recursively
    and fails on any that reached disk unescaped. The two affected records and
    their `index.json` entries are renamed in the same PR, and
    `CONTRIBUTING.md`, `manual_overrides/README.md`, and the design spec are
    updated to state the rule.
  - Acceptance criteria, met: no existing key changes, because no ISIN or
    symbol in the dataset contains `_`; the escape is applied per `/` component
    so a future `CON/A` cannot create a reserved directory; index-based
    consumers see no change, since filenames are not part of the client
    contract.
  - Automated validation: none has run. See P1 -- the PR reports
    `no checks reported`.
  - Manual validation owed on merge: `git clone` on Windows with default
    `core.protectNTFS`, which is the case that cannot be tested on the CI
    runner.
  - Evidence: **the repository cannot be cloned on Windows at all.** Git
    refuses `invalid path 'v1/stocks/CON.DE.json'` and, because it fails while
    building the index, leaves the working tree empty rather than skipping the
    two records. This working tree exists only because that check was relaxed,
    which is why it holds 98,462 shards and neither `CON` one. That is worse
    than the three validator failures recorded before the PR was found: the
    gate being red was a symptom, and a developer on Windows getting no
    checkout at all is the defect. 83,764 of 98,489 shards take their filename
    straight from an upstream ticker refreshed weekly, so any future ISIN-less
    `PRN` or `COM1` listing reintroduces it.

- [ ] **T6.** Stop a path separator in a key creating an unreachable shard.
  - Scope: the half #5 deliberately leaves alone. #5 splits a key on `/` and
    escapes each component, which keeps `BRK/A` nested by design -- its
    docstring says so. So `v1/stocks/BRK/A.json` still happens, and a nested
    record is still absent from `index.json` and still skipped by
    `validate_tree`'s one-level `glob("*.json")`. Decide between escaping the
    separator and rejecting the row, then apply it in `shard_key` on top of
    #5's shape, and report a resulting collision rather than overwriting.
  - Acceptance criteria: `BRK/A` produces one file directly under
    `v1/stocks/`; no directory remains under `v1/stocks/` or `v1/etfs/`; every
    already-valid key is byte-identical; a synthetic collision is reported and
    neither record is lost.
  - Automated validation: tests over `BRK/A`, `BF/A`, `AKO/B`, `RAC/WS`,
    `BIO/B`, plus a collision case and a regression case asserting
    `US0378331005`, `AAPL`, `BRK-A`, and `CON_.DE` are unchanged.
  - Manual validation: `python scripts/build.py --limit 2000 --out ./probe`,
    then confirm `probe/stocks/` contains no directories.
  - Dependencies or blockers: T1, and #5 -- building this before #5 merges
    means resolving the same function twice. `PLAN.md` holds the approach and
    the measurement that rules out the obvious escape character.
  - Evidence: 9 directories holding 13 records exist under `v1/stocks/`
    (`AKO`, `BF`, `BIO`, `BRK`, `CRD`, `HEI`, `HVT`, `RAC`, `WSO`). All 13 are
    committed, none is referenced by `index.json`, and none is schema-validated.
    Eleven of the 13 duplicate a dash-form shard that already publishes
    correctly, such as `BRK-A.json`; only `BIO/B` and `RAC/WS` have no
    alternate form. #5's new `validate_shard_names` uses `rglob`, so it sees
    nested paths -- but only to check them for device names, not to validate
    them against the schema.

- [~] **T7 (Phase 2, submitted early).** Resolve N-PORT filings by fund series.
  **Submitted as [#6](https://github.com/wealthfolio/asset-profiles/pull/6),
  2026-09-01. Awaiting CI approval (P1) and review.**
  - Scope as submitted: resolve a ticker to its `(CIK, series ID)` through
    SEC's `company_tickers_mf.json`, then take the newest N-PORT carrying that
    series. Series lookup reads each filing's `-index-headers.html`, about 3 KB
    and carrying `SERIES-ID`, rather than its multi-megabyte `primary_doc.xml`.
    The scan is memoised per trust and capped. Single-fund trusts -- SPY, DIA,
    GLD, SLV -- keep the existing CIK-level path unchanged. Touches only
    `scripts/build.py` and `scripts/sources/edgar.py`.
  - Acceptance criteria: four funds sharing a trust produce four different
    records. This is Phase 2's headline exit criterion, arriving before Phase 1
    closes.
  - Automated validation: none has run. See P1.
  - Manual validation owed on merge: compare `SCHD`, `SCHB`, `SCHX`, `SCHF`
    against Schwab's published breakdowns.
  - Dependencies or blockers: observing the result in published data needs P2,
    since no refresh can currently complete.
  - It also supersedes the CIK question: deriving the filer from SEC's own
    mapping makes a wrong `cik:` in the config a logged warning rather than a
    silent wrong record, and it finds **19 of the 52 configured US CIKs are
    wrong** -- #3's four, independently confirmed, plus every Select Sector
    SPDR (config points at SPDR Series Trust `0001064642`; they file under
    Select Sector SPDR Trust `0001064641`), plus VIG, VNQ, VYM, EEM, IEMG,
    QQQM, RSP, SMH, BND, VEA, VWO and VXUS.

- [ ] **T3.** Make text I/O and diagnostics platform-independent.
  - Scope: every `read_text()` and `write_text()` in `scripts/` gains an
    explicit `encoding="utf-8"` -- `build.py:335`, `build.py:339`,
    `validate.py:42`, `validate.py:120`, `validate.py:135`, `validate.py:147`.
    Replace the two non-ASCII characters the validator prints in its own error
    messages, U+2192 and U+00B1, with `->` and `+/-`.
  - Acceptance criteria: `python scripts/validate.py v1/` runs to completion on
    Windows with no `PYTHONUTF8` or `PYTHONIOENCODING` set; a record containing
    non-ASCII text is read without error.
  - Automated validation: a test that writes a fixture containing non-ASCII text
    and validates it; run under a forced cp1252 default where the platform
    allows.
  - Manual validation: run the validator on Windows in a plain console with no
    environment overrides.
  - Dependencies or blockers: T1.
  - Evidence: reading a random 4,000-shard sample raised
    `UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f`, and printing
    an index error raised `UnicodeEncodeError` on the arrow the validator puts
    in its own message. Only `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` gets the
    validator to finish on this host.

- [ ] **T4.** Make an unreachable or unvalidated shard a validator failure.
  - Scope: `validate.validate_tree` and `validate.validate_index`. Walk the
    tree rather than globbing one level, so nothing on disk escapes schema
    validation -- #5 adds a recursive `rglob` walk in `validate_shard_names`,
    but only to check names for device collisions, so reuse its walk rather
    than adding a second one. Assert that every shard on disk is named by the
    index, not only that every index path exists. Reconcile `counts` against
    both the files on disk and the distinct paths the index names. Same walk in
    `build.reap_removed` and in the re-read that feeds `build_index`.
  - Acceptance criteria: a shard on disk that the index does not name fails
    validation; the three quantities agree or the validator says which two do
    not; today's 13 nested records are reported rather than ignored.
  - Automated validation: tests over a fixture tree containing an orphan shard,
    a nested shard, and a count mismatch.
  - Manual validation: `python scripts/validate.py v1/` and confirm the nested
    records now appear in the report.
  - Dependencies or blockers: T1. Lands before T2 or after it, but the report it
    produces is what proves T2 worked.
  - Evidence: `counts.stocks` is 98,464; `index.json` names 98,463 distinct
    stock paths; 98,462 `.json` files sit directly under `v1/stocks/` and 13
    more sit one level down. Three numbers, four values, and the current
    validator reports only the one mismatch it happens to check. The
    record-to-path gap of one is unexplained and this task is where it gets
    identified.

- [ ] **T5.** Rebuild `v1/` with repaired keys and retire the nested shards.
  - Scope: one commit containing only regenerated data, after T6, T3, and T4
    have merged. Delete the 9 nested directories and their 13 records. #5
    already renames the two `CON` shards and their index entries, so those are
    not in scope here.
  - Acceptance criteria: `python scripts/validate.py v1/` exits 0 on Linux,
    macOS, and Windows from a fresh clone with no environment overrides; no
    directory remains under `v1/stocks/` or `v1/etfs/`; `git status` on a fresh
    Windows clone reports no missing files.
  - Automated validation: `validate.py v1/` in CI, and the T1 suite.
  - Manual validation: fresh `git clone` on Windows, then validate; spot-check
    that `BRK-A.json` and the repaired `BRK/A` record are not duplicates of each
    other.
  - Dependencies or blockers: **blocked, needs sign-off.** This deletes tracked
    data and rewrites tens of thousands of files. Per `AGENTS.md`, that is
    destructive work and is not implied by the pipeline fix that requires it.

### Measurements and questions owed this phase

- Why `counts.stocks` exceeds the number of distinct index paths by one. Falls
  out of T4.
- ~~Whether the weekly schedule is disabled.~~ **Answered 2026-09-02**: nine
  scheduled runs failed on a 404, 2026-06-07 to 2026-08-02, then no run at all.
  Both causes are named in P2.
- Which repository publishes to the CDN. `README.md` documents
  `wealthfolio/asset-profiles@main`; `origin` here is `rwgs/asset-profiles`.
  Owner's decision, and every client URL depends on it.

## Cross-repository work in `wealthfolio-dev`

This dataset exists to close one gap in the Wealthfolio client, and delivering
it needs work on both sides. `wealthfolio-dev/TASKS.md` is the source of truth
for the client-side bullets below -- the IDs are its own, under package
**P12B: Classification coverage**. They are restated here only as this
project's obligations and dependencies, so a change here can be checked against
what consumes it. Do not fork the detail; go read the ID.

Confirmed 2026-09-02: `grep -rn "asset-profiles\|jsdelivr"` over
`wealthfolio-dev` matches only inside `TASKS.md`. Nothing is integrated. This is
a new provider's worth of work in the client, not a switch to flip.

- [ ] **W1.** Client: give the profile model a weighted country field.
  Tracked as **I21**.
  - Scope: `AssetProfile` in `crates/market-data/src/models/profile.rs` has
    `sector` and `sectors` and only a singular `country`. `convert_profile`
    (`quotes/client.rs:837`) synthesises a one-element array from that single
    value, which is where the 100%-one-country shape originates.
  - Acceptance criteria: a weighted country array survives from provider profile
    to classification input without being collapsed to its first element.
  - Automated validation: the client's own tests.
  - Manual validation: none owed here.
  - Dependencies or blockers: none, in either repository. This is the
    prerequisite for every other bullet in this section and can start today.

- [ ] **W2.** Client: stop the region axis assigning one country at a flat 100%.
  Tracked as **I19**.
  - Scope: `ClassificationInput::from_provider_profile` keeps only
    `countries.first()`, and `auto_classification.rs:618` assigns it a flat
    10,000 bps, so a global fund is recorded as 100% one country. The sector axis
    already carries weights correctly through the same pipeline, so this is a
    port rather than a design.
  - Acceptance criteria: a fund with an eleven-country breakdown produces eleven
    weighted region assignments, not one at 100%.
  - Dependencies or blockers: W1.

- [ ] **W3.** Client: seed the 22 ISO 3166-1 countries the taxonomy omits.
  Tracked as **I29**, upstream issue #1606.
  - Scope: the seed carries 227 `country_*` ids against ISO 3166-1's 249.
    The ones that bite this dataset: `SI` Slovenia, and `JE`, `GG`, `IM` --
    common registered domiciles for LSE-listed investment trusts. A holding in
    one gets no region row at all rather than a coarse one.
  - Acceptance criteria: every alpha-2 code this dataset can publish maps to a
    region category in the client.
  - Automated validation: assert the client's seeded set covers the codes
    present across `v1/`, which this repository can produce as a list.
  - Dependencies or blockers: none. Startable today.

- [ ] **W4.** Client: read this dataset as a profile source.
  Tracked under **I20** as its chosen option.
  - Scope: per `docs/asset-profiles-spec.md` section 12 -- a profile service behind a
    source trait, a cache with a 7-day record TTL and a 1-day index TTL,
    consulted before the client's existing enrichment, with the base URL
    configurable. The resolution ladder is section 7: exact symbol, ISIN, base plus
    candidate MIC, bare base, miss.
  - Acceptance criteria: a covered fund resolves from this dataset; an uncovered
    one falls back to existing behavior; a network failure serves stale cache;
    a 404 negative-caches briefly rather than hammering.
  - Automated validation: client tests against fixtures captured from `v1/`.
  - Manual validation: a real portfolio rendering a geographic breakdown.
  - Dependencies or blockers: **blocked on this repository's Phase 3.** The
    coverage measurement below decides whether this is worth building yet.

- [ ] **W5.** Client: treat an absent weighted list as unknown, not as zero.
  - Scope: this dataset's rule is that a missing field means unknown, and
    Phase 2 will start omitting majority-synthetic lists rather than publishing
    them renormalized to 1.0. A consumer that reads absence as zero coverage
    will regress when that lands.
  - Acceptance criteria: a record with no `country_weights` leaves the client's
    region axis untouched rather than writing an empty or zeroed breakdown.
  - Dependencies or blockers: W4. Do not let this one slip behind Phase 2.

### What this repository owes the client before W4 is worth starting

- [ ] **W6.** Measure this dataset's hit rate against the client's real
  holdings, and record the number with its date and sample size.
  - Scope: take the symbol list from a real portfolio and resolve each through
    `v1/index.json`. The client's measured portfolio is 65 ETFs, mostly
    LSE-listed UCITS.
  - Acceptance criteria: a recorded hit rate, per instrument type, with the
    count of holdings that resolve to a record carrying `country_weights`.
  - Dependencies or blockers: needs the holdings list, which is user data and
    must not be committed here. Report the aggregate, not the list.
  - Expected result, and why it matters: **probably zero.** 10 of 65 universe
    entries produce a record and all 10 are US-listed; all 8 UCITS and all 5
    TSX-listed entries produce nothing. The client's own note says coverage is
    "a measurement owed" before ranking this dataset first -- this is the
    measurement, and on today's data it does not support the ranking. The fix is
    Phase 3, not a client integration.
  - Also settle: the client holds `VWRP`, the accumulating share class. The
    universe lists `VWRL` and `VWCE`. `VWRP` is not in it.

- [ ] **W7.** Publish the list of `country_code` values that appear across
  `v1/`, so W3 can be checked rather than guessed.
  - Scope: a build-time report, not a new published artifact.
  - Acceptance criteria: the list exists and excludes placeholders. `XX` appears
    in a published record today and must not survive Phase 2.
  - Dependencies or blockers: cleanest after Phase 2 rejects placeholder codes.

## Completed

Move a task here only once its acceptance criteria and required validation have
passed. Where validation was skipped, record that it was skipped and what risk
that leaves, rather than marking incomplete work done.

- [x] Repository bootstrap: licenses, disclaimer, contributing guide, three JSON
  Schemas. `4862bc3e2d`, 2026-05-09.
- [x] Stocks pipeline: FinanceDatabase loader, normalizer, validator.
  `5c9d253284`, 2026-05-09. Produces about 98,000 records.
  - Validation skipped: no tests were written. The risk that leaves is visible
    in T2 -- a shard key has been silently creating directories since this
    commit, and nothing caught it.
- [x] ETF pipeline: EDGAR primary with issuer-scraper fallback, wired into the
  build. `e77b5bb5c5`, 2026-05-09.
  - Validation skipped: no tests, and no comparison of a generated record
    against the fund's published breakdown. The risk that leaves is Phase 2's
    whole content -- ten records, of which six publish a majority fixed-income
    asset mix for an equity fund.
- [x] Weekly refresh cron and PR validation workflows. `5094b09ee0`,
  `b422e78d8d`, 2026-05-09.
  - Ran on 2026-05-09, 05-10, 05-17, 05-24, and 05-31, then stopped. 13 weeks
    with no refresh as of 2026-09-02, against a published `next_refresh_at` of
    2026-06-07. Reopened as Phase 4.
- [x] Populate the planning documents from the repository as it stands, and
  record the cross-repository work `wealthfolio-dev` needs. 2026-09-02.
  - Validation: every claim in `AGENTS.md`, `SPEC.md`, `ROADMAP.md`, and this
    file was measured against the working tree rather than read off the design
    spec. `PLAN.md` covers T2 as the next change.
