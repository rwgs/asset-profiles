# Project tasks

The work in flight and the work already validated. A task is one reviewable
outcome: if it cannot be finished and checked in a single pass, it is a phase
and belongs in `ROADMAP.md`.

Every measurement below was taken on 2026-09-02 against this working tree at
`1979d5a8c3`, on Windows with Python 3.13.9. Re-measure rather than trust a
number here once the pipeline has run again.

## Pull requests

Seven are open against `wealthfolio/asset-profiles`, all from forks, and they
cover a large part of Phases 1, 2, and 4. Read this before starting anything
below: four of the tasks in this file are already written and waiting.

| PR | What it does | Author | Opened | State |
| --- | --- | --- | --- | --- |
| [#8](https://github.com/wealthfolio/asset-profiles/pull/8) | Read and report text independently of the host locale | rwgs | 2026-09-02 | Open, CI never ran |
| [#7](https://github.com/wealthfolio/asset-profiles/pull/7) | Add a pytest harness and run it in CI | rwgs | 2026-09-02 | Open, CI never ran |
| [#6](https://github.com/wealthfolio/asset-profiles/pull/6) | Resolve N-PORT by fund series, not filer CIK | rwgs | 2026-09-01 | Open, CI never ran |
| [#5](https://github.com/wealthfolio/asset-profiles/pull/5) | Escape DOS device names in shard filenames | rwgs | 2026-09-01 | Open, CI never ran |
| [#3](https://github.com/wealthfolio/asset-profiles/pull/3) | Correct four wrong CIKs in the universe | bjmc | 2026-06-12 | Open, CI never ran |
| [#2](https://github.com/wealthfolio/asset-profiles/pull/2) | Add funds to the universe | bjmc | 2026-06-12 | Open, CI never ran |
| [#1](https://github.com/wealthfolio/asset-profiles/pull/1) | Point FinanceDatabase at its moved URLs | bjmc | 2026-06-12 | Open, CI never ran |

**Nothing has been validated by anything but review.** Every one of the six
reports `no checks reported`, and the most recent ones show GitHub run status
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
5. **#8 is order-free.** It merges clean against all six others, depends on
   none of them, and unlike #5 it flips none of #7's `xfail(strict=True)`
   cases -- all seven are `normalize.shard_key` cases and #8 touches neither
   `normalize.py` nor `test_normalize.py`. Its two tests are owed to #7 and
   are not in it, which its description states.
6. **#7 conflicts with nothing**, sharing no file with #1, #2, #3, or #6, and
   touching `CONTRIBUTING.md` in a different section from #5. But it is not
   order-free, and the interaction with #5 is **symmetric**: #7 carries two
   `xfail(strict=True)` cases over the `CON` keys, so whichever of the two
   merges second sees them reported as unexpected passes and needs them turned
   into plain assertions in its own branch first. Two lines either way, and the
   marker doing its job. Recorded on both PRs.

## Current phase

Phase 1, *A dataset that validates everywhere and hides nothing*. Three items
are already submitted, two are maintainer actions and T3 is written but not yet
sent, so the code left to write is smaller than it looks: T4, which nothing
blocks, and T6, which waits on #5 rather than resolving `shard_key` against it.

- [ ] **P1.** Get `validate-pr.yml` to run on fork pull requests.
  - Scope: a maintainer action, not a code change. Approve the pending workflow
    runs on #1, #2, #3, #5, #6, #7, and #8, and decide whether first-time fork
    contributors should stay gated. Nothing here needs a commit.
  - Acceptance criteria: `gh pr checks` reports a real result, pass or fail, on
    all seven open PRs.
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

- [~] **T1.** Add a test harness and run it in CI.
  **Submitted as [#7](https://github.com/wealthfolio/asset-profiles/pull/7),
  2026-09-02. Awaiting CI approval (P1) and review. Committed on `origin/main`
  at `4c2ad33421`, so the harness is present in this working tree.**
  - Scope as submitted: `pytest>=8.0` in `scripts/requirements.txt`, 37 tests
    under `scripts/tests/`, and a `python -m pytest scripts/tests` step in
    `validate-pr.yml` ahead of the validator, so a failure surfaces in seconds
    rather than after the minute `v1/` takes. Covers `normalize.shard_key`,
    `_aggregate_weights`, `apply_overrides`, and `validate.validate_record`.
    No production code changed.
  - Acceptance criteria, met locally: 30 passed and 7 xfailed on Python 3.13.9
    on Windows; a deliberately broken fixture fails the suite; `AGENTS.md`
    carries the real command in place of its note that none existed.
  - Automated validation: none has run. See P1.
  - Manual validation: red-then-green checked twice, and neither temporary
    change was kept. A fixture edited to make `sector_weights` sum to 1.5
    failed three tests. A simulated `shard_key` fix turned six of the seven
    strict xfails into reported unexpected passes -- and the seventh caught
    that the simulation escaped `CON.DE` to `CON.DE_` rather than `CON_.DE`,
    which is the wrong fix.
  - Validation owed on merge: `pytest` resolving from
    `scripts/requirements.txt` on the runner is unproven, since the CI step has
    never executed. The risk that leaves is a green local suite and a red first
    CI run. Locally the suite ran against `pytest`, `jsonschema`, `pycountry`,
    and `pyyaml` installed on their own, because the full requirements do not
    install on this host -- see T8.
  - Dependencies or blockers: none. It was the prerequisite for T3, T4, and T6,
    which are now unblocked whatever upstream does with #7.

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
    `no checks reported`. #7 carries two `xfail(strict=True)` cases over `CON`
    and `CON.DE`, so whichever of #5 and #7 merges second reports them as
    unexpected passes and owns turning them into plain assertions. Two lines.
  - Owed on merge, and larger than that flip: **#5's stated test coverage is
    not in the tree.** Its description reports 16 `shard_key` cases and a
    `validate_shard_names` fixture, but its diff adds no test file, so nothing
    re-runs any of it. #7 gives them a home, so committing them alongside the
    xfail flip is what makes the claim in #5's description true. This matters
    more here than elsewhere: 83,764 of 98,489 shards take their filename
    straight from an upstream ticker refreshed weekly, so the next `PRN` or
    `COM1` listing is a data event rather than a code change.
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
    `US0378331005`, `AAPL`, `BRK-A`, and `CON_.DE` are unchanged. #7 already
    wrote the first five as `xfail(strict=True)`, asserting only that the
    result holds no separator; this task turns them into plain assertions on
    the exact expected key and adds the rest.
  - Manual validation: `python scripts/build.py --limit 2000 --out ./probe`,
    then confirm `probe/stocks/` contains no directories.
  - Dependencies or blockers: #5 -- building this before #5 merges means
    resolving the same function twice. `PLAN.md` holds the approach and
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

- [~] **T3.** Make text I/O and diagnostics platform-independent.
  **Submitted as [#8](https://github.com/wealthfolio/asset-profiles/pull/8),
  2026-09-02. Awaiting CI approval (P1) and review. Committed on `origin/main`
  at `14cc37b1c1`, so this working tree has it and T4 can be written on a
  correct base.**
  - Branch: `fix/locale-independent-text-io` at `5e3bebd189`, cut off
    `upstream/main` and holding only `validate.py` and `build.py` -- the split
    T1 used, with neither planning document. Verified to merge clean against
    all six others, and its two blobs are byte-identical to the gate-verified
    versions on `main`. GitHub reports it `MERGEABLE` over two files.
  - **The two tests are not on that branch, and cannot be.** `scripts/tests/`
    does not exist on `upstream/main`, so a branch cut from there has nowhere
    to put them -- and a tests-only branch is red by construction, since both
    assert the fixed behavior. Measured: reverting `validate.py` to the
    revision `upstream/main` still carries makes both fail. So they are owed to
    #7, which adds the harness that hosts them, and the PR says so rather than
    implying coverage it does not ship. This is the same debt recorded above
    against #5, disclosed instead of discovered.
  - Deliberately not stacked on #7. A branch based on `test/pytest-harness`
    would carry the tests, but its PR silently includes #7's six files until #7
    merges, so a maintainer merging this one would merge #7's CI step and
    requirements change without being asked. Given how carefully the merge
    order above is tracked, hiding one PR inside another is the worse trade.
  - It waits on nothing and blocks nothing, so it was sent without waiting
    for #7. Its description ranks it last on purpose: #1 is why the dataset is
    stale, #6 fixes six wrong ETF records and #5 makes the repository cloneable
    at all, while this one only ever bites a contributor on a non-UTF-8 host --
    which is why CI has never reported it.
  - Validation owed on merge: the two tests, once #7 lands. Nothing else --
    unlike #7, the change itself is verified locally on the platform it is
    about, which is the platform CI cannot provide.
  - Delivered: `encoding="utf-8"` on the six `read_text()` calls that had none
    -- `validate.py` 42, 120, 133, 146 and `build.py` 335, 339 -- and the
    validator's own messages reduced to ASCII. **Three characters, not the two
    this task's scope named:** `+/-` for U+00B1 and `->` for U+2192 as written,
    plus `<=` for U+2264 in the `top_holdings` message, which is printed by the
    same report and would have kept the gate red on its own. No production
    behavior changed beyond the encoding: no record, path, or URL moved.
  - Acceptance criteria, met: `python scripts/validate.py v1/` now runs to
    completion on Windows with no `PYTHONUTF8` or `PYTHONIOENCODING` set -- 82
    seconds over 98,462 shards, reporting only the three pre-existing `CON`
    failures #5 owns. Before the change the same command died after 3.5 seconds
    on `UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f`, having
    validated nothing and printed nothing.
  - Automated validation: two tests added to `scripts/tests/test_validate.py`,
    and an `index_of` fixture in `conftest.py` that builds the smallest index
    the schema accepts. 32 passed and 7 xfailed, up from 30 and 7. Red-then-green
    checked by reverting `validate.py` to `HEAD` and re-running: both new tests
    failed, the other 30 passed, and the file was restored byte-identical.
    - A shard whose name carries byte 0x8F -- undecodable in cp1252, and the
      byte the `v1/` sample actually failed on -- validates through
      `validate_tree`.
    - Every message the validator writes itself is ASCII. Values inside a
      message can be non-ASCII, since they come from the data; the templates
      around them cannot.
  - Manual validation: `build.py --no-stocks --no-etfs --out <dir>` over two
    non-ASCII shards, which skips both fetch passes and reaches nothing but the
    index rebuild, so it exercises `build.py`'s two lines with no network. It
    crashed on the same 0x8f before the change and rebuilt the index cleanly
    after, with a Japanese name intact through the read.
  - Also available now, and recorded in `AGENTS.md`:
    `python -X warn_default_encoding -W error::EncodingWarning scripts/validate.py v1/`
    names the offending line if a future call starts relying on the host locale.
    It was what located all six sites.
  - Why the build's log lines were left alone, measured rather than assumed:
    `logging` catches the encode failure and falls back to backslashreplace, so
    `edgar.py:83`'s `ticker->CIK` arrow prints as `ticker→CIK` and the run
    continues at exit 0. `print()` raises and takes the process with it. Only
    the validator reports through `print()`, so only its messages had to change
    -- and a future diagnostic added with `print()` needs the same care.
  - Not fixed, and deliberately out of scope: a `jsonschema` message quoting a
    non-ASCII record value is still printed verbatim, so a schema failure on a
    record with an accented name can still raise `UnicodeEncodeError` on a
    cp1252 console. No such failure exists in `v1/` today -- the gate's only
    three errors are the ASCII `CON` ones -- and suppressing it means either
    forcing the stream encoding or mangling the value, both of which change how
    every diagnostic reads. Raised rather than folded in.

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
  - Dependencies or blockers: none; #7 carries the harness. Lands before T2 or
    after it, but the report it produces is what proves T2 worked.
  - **Base this on T3, not on `upstream/main`.** T4 rewrites the exact lines T3
    changed: `validate.py` 120 and 133 are inside the two read loops it merges
    into one walk, 94 and 99 are in the `validate_index` it extends, and
    `build.py` 335 and 339 are the re-read named in the scope above. A branch
    cut off `upstream/main` writes that new walk against the unfixed base and
    silently drops `encoding=` back out -- undoing T3 inside the function that
    replaces it. Cut it from `main` after T3, or base it on T3's branch.
  - Keep it a separate PR from T3 rather than folding the two together, for a
    review reason: T3 is mechanical and obviously correct, while this changes
    what the gate *fails on* -- the 13 nested records start failing, which
    someone has to accept as a decision. Bundling makes the trivial fix hostage
    to review of the contentious one. Order is #7, then T3, then T4; all three
    extend `scripts/tests/test_validate.py`.
  - Evidence: `counts.stocks` is 98,464; `index.json` names 98,463 distinct
    stock paths; 98,462 `.json` files sit directly under `v1/stocks/` and 13
    more sit one level down. Three numbers, four values, and the current
    validator reports only the one mismatch it happens to check. The
    record-to-path gap of one is unexplained and this task is where it gets
    identified.

- [ ] **T8.** Decide what to do about the numpy ceiling `etf-scraper` drags in.
  - Scope: `etf-scraper>=0.1.2` requires `numpy<2.0`, which publishes no wheel
    for Python 3.13, so `uv pip install -r scripts/requirements.txt` tries to
    compile numpy from source and fails on any host without a C toolchain.
    Choose between pinning the project to 3.12, replacing the dependency with
    direct issuer fetches through `http_cache`, and carrying it as an optional
    extra. Raised while doing T1 rather than acted on: it settles a dependency
    question, so ask first.
  - Acceptance criteria: the documented setup command succeeds on the current
    stable Python, or the documentation names the version it requires and why.
  - Automated validation: the CI install step, run on both 3.12 and 3.13.
  - Manual validation: a clean `uv venv` and install on Windows.
  - Dependencies or blockers: none, and it blocks nothing. The tests do not
    import it and neither does the stocks pass.
  - Evidence: measured 2026-09-02 on Python 3.13.9, Windows. `pip install
    etf-scraper` resolves `numpy<2.0` and dies in meson looking for a compiler.
    CI is unaffected -- it pins 3.12, where numpy 1.26 has a wheel -- which is
    why nine failing scheduled runs never reported it. `issuer_scraper.py` is
    the only importer, it imports lazily inside the fetch function, and it is
    the non-US fallback that produces no records at all today.

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
