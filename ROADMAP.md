# Project roadmap

Ordered outcomes, each one leaving the project in a working state. A phase is a
result rather than a batch of work: if finishing it does not change what the
project can do, it belongs inside another phase. Phases are also the unit that
gets reordered when priorities change, so keep them independent enough to
reorder.

The pipeline, the schemas, the workflows, and a 98,000-record stock dataset all
exist and shipped between 2026-05-09 and 2026-05-31. What follows starts from
there, not from zero. Phases 1 to 4 land in this repository; Phase 5 lands in
`wealthfolio-dev` and is tracked here because it is the outcome this dataset
exists to enable.

Seven pull requests are open upstream and they already carry parts of Phases 1,
2, and 4 -- including Phase 2's headline exit criterion and the test harness.
None has been through CI, because fork PRs are gated behind approval that has
never been given, and upstream has since said the repository is on standby. So
work lands on `origin/main` and each change also keeps an upstream-mergeable
branch. See the pull-requests section of `TASKS.md` for the merge order and
`AGENTS.md` for why.

## Phase 1: A dataset that validates everywhere and hides nothing

**Substantively reached on 2026-09-03, on `origin/main`.** `validate.py v1/`
exits 0, the suite is 71 passed, nothing is nested, and the three counts agree.
The one criterion outstanding is the CI one, and no fork can supply it -- see
below.

### Outcome

`python scripts/validate.py v1/` exits 0 on Linux, macOS, and Windows from a
fresh clone with no environment variable set to make it work, and no record can
be present on disk without being validated and reachable from the index. Today
a Windows `git clone` fails outright and leaves an empty tree, 13 records sit
in nested directories that the validator's schema pass never sees, and the
validator cannot print its own errors in a cp1252 console.

**Partly written already.** PR #5 fixes the clone failure and adds a recursive
name check. What remains is the path separator, the encoding, the schema pass
over nested records, and the tests.

### Included work

- Make a shard key safe as a single filename before it reaches the filesystem:
  escape path separators, escape Windows reserved device names, and fail on a
  collision instead of overwriting.
- Read and write text as UTF-8 explicitly in `build.py` and `validate.py`, and
  keep diagnostics printable in a cp1252 console.
- Make the validator see everything on disk, so an unreachable or unvalidated
  shard is a failure rather than an absence.
- Reconcile `counts` with both the shards on disk and the distinct paths the
  index names, and identify the current one-record gap.
- Add a test harness and wire it into `validate-pr.yml`, with the observed
  upstream keys `BRK/A` and `CON` as its first cases.

### Dependencies and risks

- Repairing the keys renames shards, so `v1/**` is rewritten. That is a
  destructive, unreviewable diff and must be a separate commit from the pipeline
  change that causes it.
- The 13 nested records are committed. Removing them is deletion of tracked
  data, so it needs explicit sign-off even though nothing can read them.
- Risk: an escaping scheme that changes an existing well-formed key silently
  breaks every client-cached path. It bites if escaping is applied to all keys
  rather than only to keys the filesystem rejects.

### Exit criteria

- [~] The validator exits 0 on all three platforms on a fresh clone. **Met on
  Windows**, verified 2026-09-03 with no environment overrides and again under
  `-W error::EncodingWarning`. Linux and macOS are unverified in this checkout;
  the remaining platform risk is small, since T3 removed the only
  locale-dependent reads and the paths are now plain ASCII filenames.
- [x] No path under `v1/stocks/` or `v1/etfs/` is nested, and no stem matches a
  Windows reserved device name. T6 stopped them being created; T5's minimal
  route retired the 13 that existed; #5 renamed the two `CON` shards.
- [x] Shard count on disk, `counts`, and distinct index paths all agree, at
  98,463 stocks and 10 ETFs.
- [ ] CI runs the tests on every pull request and the tests fail if `BRK/A` or
  `CON` regresses. **The step is written and has never executed.** Fork PR runs
  are gated behind maintainer approval on a repository that is on standby, so
  this criterion cannot be met from here. The tests themselves are real: both
  cases are plain assertions in the suite, and both were confirmed red before
  their fixes landed.

### Validation

- Automated: the new test suite; `validate.py` against a `--limit` build tree;
  `validate.py v1/` in CI.
- Manual: run the validator on Windows without `PYTHONUTF8`, and confirm a fresh
  `git clone` on Windows produces no missing-file report.

## Phase 2: ETF records that describe the fund they name

**Current, and opened on 2026-09-03** when its headline change merged into
`origin/main`. Three of the other four landed the same day; one is left, and it
is the only one that changes what the dataset publishes rather than how it is
built.

### Outcome

Each fund's record reflects that fund's own holdings, and a weighted list is
published only when it carries signal. Today four Schwab funds in one trust
carry byte-identical holdings, `SCHD` -- an equity fund -- is recorded as 98%
fixed income, six of the ten publish `sector_weights` that are 100% `Unknown`
at a valid-looking sum of 1.0, and `SPY`'s are 30% `Unknown`.

### Included work

- Select the N-PORT filing by fund series, not by filer CIK. 42 of 65 universe
  entries share a CIK with another entry, so the current lookup cannot tell them
  apart. **Written and submitted as PR #6**, which also finds that 19 of the 52
  configured US CIKs name the wrong filer, and makes the config's CIK advisory
  rather than load-bearing. **Merged into `main` at `52fdc78ce3`, 2026-09-03**,
  with the tests it owed at `55db8b4e0b`. Still open upstream.
- Resolve a holding's sector through CUSIP and ticker as well as ISIN. Only
  about 15% of stock records carry an ISIN, which is why the lookup mostly
  misses. **Done at `b8806b695d`, 2026-09-03.** The ticker leg was already
  there and is nearly useless for an EDGAR fund -- of 4,857 live holdings
  across six funds, 4,845 carry an ISIN and 1 carries a ticker. CUSIP is the
  leg that reaches the rest: resolved sector weight moves SCHD 87.0% to 98.5%
  and SPY 69.0% to 79.6%.
- Reject placeholder country codes. `XX` reaches a published record today
  because the schema checks the shape of a code and not its existence.
  **Done at `790b45e584`, 2026-09-03**, at the source and in the validator.
  Four published records carry one, so the gate is red on them until a rebuild
  runs.
- Omit a weighted list that is majority-synthetic instead of renormalizing
  `Unknown` to 1.0, and add the validator rule that makes shipping one an error.
- Report per-fund coverage from the build: unknown share per axis, and every
  universe entry that produced no record with the reason why. **Done at
  `209ddb2343`, 2026-09-03.**

### Dependencies and risks

- Depends on Phase 1: without a trustworthy gate, a data fix cannot be shown to
  have worked.
- Series-level selection needed a series-to-ticker mapping. Resolved: SEC
  publishes `company_tickers_mf.json`, 28,512 share classes, and PR #6 reads
  each filing's 3 KB `-index-headers.html` for its `SERIES-ID` rather than its
  multi-megabyte `primary_doc.xml`.
- The result of #6 cannot be seen in published data until the refresh runs
  again, which is Phase 4's first item. Merging #6 without that leaves the
  fix true in the code and invisible in the dataset.
- Risk: omitting majority-unknown lists visibly reduces what the dataset
  publishes. It bites if a consumer already treats a present-but-meaningless
  list as coverage, which is why Phase 5's client work must read absence as
  unknown.

### Exit criteria

- [x] Four funds sharing one CIK produce four different records, each matching
  its own published holdings. **Met, and against live EDGAR rather than
  fixtures**, 2026-09-03. Refetching SCHD, SCHB, SCHX and SCHF gives four
  different filings, each recognisably its own fund: SCHD 102 holdings led by
  QUALCOMM, Texas Instruments and UnitedHealth; SCHB 2,411 led by NVIDIA,
  Apple and Microsoft; SCHX 751 of the same mega-caps; SCHF 1,479 led by
  Samsung, SK hynix and ASML with 6 US holdings across 32 countries. All four
  are 99% Equity, where the published records say 98% Fixed Income. That also
  proves what the fixtures could not: a real `-index-headers.html` matches the
  regex and a real multi-megabyte N-PORT parses.
- [ ] No published weighted list is majority-synthetic. **The one item left.**
- [~] Every published `country_code` resolves in `pycountry`. The rule exists
  and no new record can carry an unassigned code; the four already published
  fail it until a rebuild.
- [x] The build reports each universe entry as a record or a named failure.

### Validation

- Automated: tests over fixture N-PORT XML covering a multi-series trust, a
  placeholder country code, and a holdings set with no resolvable sectors; the
  new validator rules. **The multi-series trust is done**, against a fake HTTP
  layer rather than captured filings -- so it covers the selection and not the
  parse of a real N-PORT.
- Manual: compare `SCHD`, `SCHB`, `SCHX`, and `SCHF` against Schwab's published
  breakdowns, and `SPY` against the S&P 500's known sector split.

## Phase 3: Coverage that matches the portfolios being described

### Outcome

The dataset covers the funds real portfolios hold, measured rather than assumed,
and the non-US path produces records. Today 10 of 65 universe entries produce a
record and all 10 are US-listed; all 13 non-US entries -- 8 UCITS and 5
TSX-listed -- produce nothing, which is the half the consuming client actually
needs.

### Included work

- Make the issuer fallback work end to end for one UCITS fund, then for the rest
  of the non-US universe.
- Measure the hit rate against the consuming client's real holdings and record
  the number, not an impression.
- Settle whether share classes need separate entries: the client holds `VWRP`
  and the universe lists `VWRL` and `VWCE`.
- Grow the universe against that measurement rather than against a target count.

### Dependencies and risks

- Depends on Phase 2: adding funds to a pipeline that conflates them multiplies
  wrong records rather than adding right ones.
- `etf-scraper` does not expose a session hook, so issuer fetches bypass
  `http_cache.py` and its rate limiting. Volume is currently held down only by
  how few funds are scraped, which stops being true in this phase.
- Risk: issuer pages move and a scraper that worked last week returns nothing.
  It bites silently unless Phase 2's per-fund failure report is in place first.
- Risk: the measurement shows the universe is the wrong shape for the consuming
  portfolio, which reopens the target rather than extending it. Better found
  here than after 300 entries.

### Exit criteria

- At least one UCITS fund publishes `country_weights` sourced from its issuer.
- The hit rate against the client's holdings is recorded in `TASKS.md` with the
  date and the sample size.
- Every universe entry either produces a record or carries a recorded reason it
  cannot.

### Validation

- Automated: tests over a captured issuer holdings file, so the parser is tested
  without a live fetch.
- Manual: fetch a UCITS record over the CDN and compare its country weights
  against the issuer's own factsheet.

## Phase 4: A published dataset that is as fresh as it claims

### Outcome

The dataset served over the CDN is current, and its `next_refresh_at` is a
commitment rather than a claim. Today the last refresh committed on 2026-05-31,
the published `next_refresh_at` was 2026-06-07, and both are months past.

### Included work

- Merge PR #1 and re-enable the schedule. **Why it stopped is established**:
  nine scheduled runs failed on a 404 between 2026-06-07 and 2026-08-02 after
  FinanceDatabase moved its CSVs to `compression/*.bz2`, then the schedule
  stopped firing at all, consistent with GitHub's 60-day inactivity disable.
  Two causes, and #1 addresses only the first.
- Add a check that fails when the published dataset is past its own
  `next_refresh_at`, so silence is loud.
- Settle which repository publishes, since `README.md` documents CDN URLs
  against `wealthfolio/asset-profiles` and the work is on `rwgs/asset-profiles`.
- Cut `v1.0.0` and set the tagging cadence. `README.md` already documents pinned
  `@v1.0.0` URLs, which 404 today.
- Correct the setup command in `README.md` and `CONTRIBUTING.md`, which fails
  without an active virtualenv, and the `manual_overrides/README.md` claim of a
  no-op override warning the build does not emit.

### Dependencies and risks

- Publishing should follow Phases 1 and 2, so what gets tagged is worth pinning.
- Risk: restarting the schedule against an unrepaired pipeline republishes the
  same wrong ETF records weekly and refreshes their `fetched_at`, which makes
  them look verified. Merging #6 before restarting avoids it.
- Risk: nine identical failures ran unremarked for two months, so nothing
  currently notices. The freshness check is what closes that, not the fix.
- Deciding the publishing repository is a project question, not an
  implementation one, and belongs to the owner.

### Exit criteria

- A refresh commit lands on the published branch on schedule, unprompted.
- A dataset past its own refresh date fails a check rather than passing quietly.
- `v1.0.0` exists and the pinned URLs in `README.md` resolve.
- Every command in `README.md` and `CONTRIBUTING.md` runs as written.

### Validation

- Automated: the freshness check, running on its own schedule.
- Manual: fetch `index.json` from jsDelivr and confirm `generated_at` moved;
  fetch a pinned tag URL and confirm it resolves.

## Phase 5: Consumed by the client

### Outcome

A Wealthfolio user holding a fund sees its geographic breakdown. This is the
outcome every phase above serves, and none of them delivers it: the dataset is
not integrated in the client in any form.

The work lands in `wealthfolio-dev`, under its `P12B` package. It is tracked
here because this repository is the dependency, and because two of its bullets
are blocked on nothing this repository does and can start immediately.

### Included work

- Not blocked on this repository, and startable now: give the client's profile
  model a weighted country field, and stop the region axis assigning one country
  at a flat 100%. Seed the 22 ISO 3166-1 countries the client's taxonomy omits.
- Blocked on Phase 3: a profile source that reads this dataset, its cache, and
  the wiring that consults it before falling back to the client's own
  enrichment.
- Blocked on Phase 2: treating an absent weighted list as unknown rather than as
  zero coverage.

### Dependencies and risks

- Depends on Phase 3 for whether the dataset covers the holdings in question,
  and on Phase 4 for whether what it covers is current.
- Risk: the client integrates against a dataset whose UCITS coverage is zero, so
  the feature ships and changes nothing for the portfolios that needed it. This
  is why Phase 3's measurement comes before the wiring.
- Risk: two repositories, one outcome. Neither side's tests catch a contract
  mismatch, so the schema is the only shared artifact and a change to it is a
  cross-repository event.

### Exit criteria

- Region coverage in the client, measured against a real portfolio, moves off
  5.2%.
- A fund with no entry in this dataset degrades to the client's existing
  behavior rather than to an empty breakdown.

### Validation

- Automated: the client's own tests, against fixtures captured from this
  dataset.
- Manual: a real portfolio of LSE-listed UCITS funds rendering a geographic
  breakdown, with a screenshot.
