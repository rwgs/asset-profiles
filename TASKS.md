# Project tasks

The work in flight and the work already validated. A task is one reviewable
outcome: if it cannot be finished and checked in a single pass, it is a phase
and belongs in `ROADMAP.md`.

Most measurements below were taken on 2026-09-02 on Windows with Python 3.13.9,
against this working tree at `1979d5a8c3` or, for T4's, at `2a76205957`. The two
differ only in `scripts/` and the planning documents, so no figure about `v1/`
moved between them. P2's are newer: 2026-09-03 at `ccab4c6f78`, on Python
3.14.5 with every requirement except `etf-scraper` installed -- which is T8's
subject and does not touch the stocks pass. T7's are newer again: 2026-09-03 at
`55db8b4e0b`, same host and interpreter. T9 through T12's are newer again:
2026-09-03 at `6e83a572e6`, same host, and they are the first taken against
**live EDGAR** with `SEC_USER_AGENT` set. Re-measure rather than trust a number
here once the pipeline has run again.

## Pull requests

Seven are open against `wealthfolio/asset-profiles`, all from forks, and they
cover a large part of Phases 1, 2, and 4. Read this before starting anything
below: four of the tasks in this file are already written and waiting.

| PR | What it does | Author | Opened | State |
| --- | --- | --- | --- | --- |
| [#8](https://github.com/wealthfolio/asset-profiles/pull/8) | Read and report text independently of the host locale | rwgs | 2026-09-02 | Open, CI never ran |
| [#7](https://github.com/wealthfolio/asset-profiles/pull/7) | Add a pytest harness and run it in CI | rwgs | 2026-09-02 | Open, CI never ran |
| [#6](https://github.com/wealthfolio/asset-profiles/pull/6) | Resolve N-PORT by fund series, not filer CIK | rwgs | 2026-09-01 | Open upstream, CI never ran; **merged into `main`** |
| [#5](https://github.com/wealthfolio/asset-profiles/pull/5) | Escape DOS device names in shard filenames | rwgs | 2026-09-01 | Open upstream, CI never ran; **merged into `main`** |
| [#3](https://github.com/wealthfolio/asset-profiles/pull/3) | Correct four wrong CIKs in the universe | bjmc | 2026-06-12 | Open, CI never ran |
| [#2](https://github.com/wealthfolio/asset-profiles/pull/2) | Add funds to the universe | bjmc | 2026-06-12 | Open, CI never ran |
| [#1](https://github.com/wealthfolio/asset-profiles/pull/1) | Point FinanceDatabase at its moved URLs | bjmc | 2026-06-12 | Open upstream, CI never ran; **merged into `main`** |

**Upstream is on standby and none of this will be merged soon.** Asked about #5
on 2026-09-03, `afadil` replied: *"this repo is not used at all, it was an idea
to curate stock and symbol profiles. but it's en stand by"*. That is the answer
to the CDN question this file has been carrying, and it reframes everything
below: P1 and P2 are not cheap wins waiting on a button, they are requests to a
maintainer who has said they are not working on this. Nothing here is withdrawn
-- the defects are real and the changes are written -- but the plan is now to
land work on `origin/main` and keep each change on an upstream-mergeable branch
against the day that changes.

**Nothing has been validated by anything but review.** Every one of the seven
reports `no checks reported`, and the most recent ones show GitHub run status
`action_required` at 0s duration: `validate-pr.yml` is gated behind maintainer
approval for fork pull requests, so the repository's only automated check has
never executed against any proposed change. P1 below is what would fix that, and
it is now known to be unlikely rather than merely unattempted.

**Merge order matters, and GitHub will not warn about it.**

1. **#1 first.** Until it lands every scheduled refresh fails, so no other
   change can be observed in the published data. See P2. **Merged into `main`
   at `ccab4c6f78`, 2026-09-03**, and verified against the live source rather
   than on review -- so the pipeline runs here even though the published
   dataset is still stale.
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
   **Merged into `main` at `52fdc78ce3`, 2026-09-03**, with the tests it owed
   committed alongside at `55db8b4e0b`. Its one line of `build.py` auto-merged
   clean over T4's and T6's rewrite of that file, and `edgar.py` was untouched
   on `main`, so the branch landed whole.
4. **#5 is independent** of all of the above.
5. **#8 is order-free.** It merges clean against all six others, depends on
   none of them, and unlike #5 it flips none of #7's `xfail(strict=True)`
   cases -- all seven are `normalize.shard_key` cases and #8 touches neither
   `normalize.py` nor `test_normalize.py`. Its two tests are owed to #7 and
   are not in it, which its description states.
6. **#7 conflicts with nothing among the PRs**, sharing no file with #1, #2,
   #3, or #6, and touching `CONTRIBUTING.md` in a different section from #5. But
   it is not order-free, and the interaction with #5 is **symmetric**: #7
   carries two `xfail(strict=True)` cases over the `CON` keys, so whichever of
   the two merges second sees them reported as unexpected passes and needs them
   turned into plain assertions in its own branch first. Two lines either way,
   and the marker doing its job. Recorded on both PRs.
7. **T8's branch conflicts with #7**, and it is the only conflict either has.
   Both edit the last line of `scripts/requirements.txt`: #7 appends a `# tests
   only` block below `etf-scraper>=0.1.2`, and T8 replaces that same line with
   the comment explaining where the dependency went. Verified with
   `merge-tree`, which reports every other pairing clean. The resolution is to
   keep both blocks, and it is already written -- `main` holds exactly that
   file. Whichever lands second copies it.

## Current phase

Phase 2, *ETF records that describe the fund they name*, opened on 2026-09-03
when its headline change landed on `main`: T7, submitted upstream as #6, plus
the tests it owed. Nothing else in Phase 2 has started, and the four remaining
items are listed under it in `ROADMAP.md`.

Phase 1 is behind it, and **every task in it that can be done from a fork is
done**. T1 and T3 are written and submitted; T2, T4, T6, T8, and the signed-off
half of T5 are on `main`; #1, #5, #6, and #8 are merged there too.

The headline is that `python scripts/validate.py v1/` **exits 0** -- on Windows,
under the locale-strict form, with no environment overrides -- and the suite is
78 passed with no strict markers left. Both numbers were red or absent a week
ago. What made that true, in order: T1 gave the project a suite, #5 made it
clone on Windows, T3 made it run on a non-UTF-8 host, T4 made an unreachable
shard a failure, T6 stopped new ones being created, and T5's minimal route
retired the 14 that already existed.

**Phase 1 still cannot close as written**, and that is a property of upstream
rather than of the work. Its exit criteria assume merges, a CI run, and a
refresh, and all three need a maintainer who has said the repository is on
standby. Nothing in this checkout can supply them.

**Phase 2 is closed**, on 2026-09-03, the day it opened. T9 through T13
landed and `v1/` was rebuilt twice -- T14, then again to apply T13's rule -- so
all four exit criteria are met in the published data rather than only in the
code. `python scripts/validate.py v1/` **exits 0**.

Phase 3 has not been opened. `ROADMAP.md` has the phase order; T15, the
identifier bridge, is the highest-value follow-on and is written up below.

**`v1/` was rebuilt, and `SCHD` now reads as its own fund**: 99.95% Equity
against the 98.0% Fixed Income it published for three months, 102 holdings led
by QUALCOMM, Texas Instruments and UnitedHealth. 49 ETF records against 10, and
`generated_at` finally off 2026-05-31. See T14.

**This fork now publishes.** Answered 2026-09-03 and recorded in `DECISIONS.md`:
`README.md` points jsDelivr at `rwgs/asset-profiles@main` and the weekly
refresh is this repository's obligation. That unblocks the half of P2 that was
waiting on a maintainer, and it makes the rebuild below a scheduled event
rather than a hypothetical.

So what remains here is not Phase 1 code:

- **P1 is a maintainer action** and stays blocked: approving CI on the seven
  open PRs needs write access on a repository that is on standby. **P2's
  refresh half is no longer blocked** -- the schedule that matters is this
  fork's, and it needs `SEC_USER_AGENT` set as a repository secret plus
  sign-off on the rebuild.
- ~~The published dataset is still stale.~~ **Refreshed 2026-09-03 by T14 and
  again by T16.** `generated_at` is 2026-09-03 and `next_refresh_at`
  2026-09-10, and that is now a commitment this repository has to keep.
- ~~`SEC_USER_AGENT` is not set as a repository secret.~~ **Set 2026-09-03 at
  08:13Z**, confirmed with `gh secret list`. The scheduled refresh can now
  complete, and the next Sunday 06:00 UTC run is the first test of it
  end to end on a runner.
- **The rebuild shrank the dataset, and the reason was measured, not
  assumed.** 90,513 stock records against 98,463, and 8,730 index symbols stop
  resolving -- **every one of them absent from FinanceDatabase upstream too**,
  checked against the 112,651 symbols it publishes today. None was dropped by
  this pipeline. Anything holding one of those paths breaks, and that was the
  cost signed off.
- **ETF coverage went from 10 records to 49**, of 65 universe entries. #6's
  series resolution finds the filings a CIK-level lookup could not, and the
  negative-weight fix admits the 11 funds the schema had been rejecting. The
  16 with no record are each named with a reason in the build log.
- **Both open questions are answered**, 2026-09-03. See the questions section.
- **W6 through W9** are what this repository owes the client. W6 needs holdings
  data that must not be committed here; W8 and W9 were added 2026-09-03 and are
  the shape of the published index rather than its contents.
- **Five listing-metadata and vocabulary defects were found in the published
  tree**, 2026-09-03, while scoping W4 -- see the client-integration findings
  below. 17.4% of listings name a venue they are not on. They are the reason
  W4 should not start on today's `v1/`: the client's own P10C package exists on
  the finding that a wrong MIC is worse than an absent one.
- **#6 is now proven against live EDGAR**, not only against fixtures -- see T7,
  which this closes. It still cannot be seen in the published data until a
  refresh runs.
- **T18's measurement is done, 2026-09-03, and it found a second defect the
  task was not looking for.** 2,142 records carry an ISIN whose country prefix
  disagrees with their own `country_code` -- 22.9% of the 9,356 that have an
  ISIN, and every one of them already wrong in FinanceDatabase rather than
  introduced here. Inside that count, **164 records are keyed by an ISIN that
  belongs to a different company**, because the source joined on a bare ticker:
  AAR Corp. is published as Clean Air Metals' ISIN. That is now T19, and it is
  a worse defect than the receipt keying T18 was raised for. Also worth
  carrying forward: only **9,356 of 90,513** stock records have an ISIN at all,
  against `DECISIONS.md` making ISIN the canonical key.
- **OpenFIGI is adopted, and putting all 9,356 published ISINs to it replaced
  three heuristics with typed answers.** T18's extent is **445** records keyed
  by a depositary receipt's ISIN, not the 2 it was raised for -- NVIDIA,
  Netflix and Walmart among them, each keyed by its Canadian receipt. T19's is
  **104 confirmed**, down from the detector's 164. And a question nobody
  asked got answered: **445 `EURO-ZONE` structured certificates, 108 ETPs and
  69 funds are published as stock records**, which is now T20.
- **GLEIF was measured too, and it half-works.** A receipt's ISIN maps to the
  *issuer's* LEI -- Nestle's ADR and its Swiss ordinary share one -- so the
  join is exact. But 1,365 of T18's 2,142 are not in the file, only 176 gain a
  local ISIN, and Hon Hai and TSMC's Taiwan lines are absent entirely. It
  closes 8.2% of the class and misses the cases it was wanted for.

- **The four open data-defect questions were put to the owner and three were
  answered, 2026-09-03.** T19 drops a wrong ISIN and re-keys the record by
  symbol; T20 keeps a non-equity record but corrects its `kind` and strips the
  sector it inherited; T15 waits for a source carrying TSMC's Taiwan line
  rather than aliasing it to the ADR. Both implemented rules are on `main`,
  suite at 221 passed and `validate.py v1/` still exit 0. T15's provenance
  question is the one still open, and holding T15 means nothing waits on it.
- **The sweep that answered them typed all 9,400 published ISINs and
  partitions into two counts**, both measured against the shipped rule rather
  than an earlier heuristic: **322 records keyed by another company's ISIN**
  and **571 non-equities, 554 of which publish a sector they do not have**.
  The earlier figures in T18, T19 and T20 -- 104, 164, 622 -- were floors from
  narrower detectors and should not be quoted, and neither should the **615**
  this bullet carried until 2026-09-03: it swept the index's 9,400 ISINs,
  which include the 44 belonging to ETF records that are already correctly
  typed in `v1/etfs/`. See T20.
- ~~`v1/` has not been rebuilt, so every defect above is still published.~~
  **Rebuilt 2026-09-03 with sign-off -- see T22.** `diff: +322 / ~90240 /
  -322`, counts unchanged at 90,513 stocks and 49 ETFs, index ISINs down to
  9,078, and `validate.py v1/` exit 0. So 322 records no longer wear another
  company's identifier and 554 no longer publish a sector they do not have, in
  the data rather than only in the code. **322 published URLs stopped
  resolving and 322 started**, which is what a re-key costs and what was
  signed off.
- **The refresh timeout moved from 45 minutes to 90, and `OPENFIGI_API_KEY` is
  now set** -- 2026-09-03 at 20:59Z, confirmed with `gh secret list`. The ISIN
  sweep is 94 requests and under a minute with it, against 940 requests and
  about 39 minutes on the cold cache CI always has, so the expected run is
  well inside 45; the ceiling stays at 90 because it is sized for the key
  being absent or revoked rather than for the happy path. **The key's value
  has never been exercised anywhere**, so Sunday 06:00 UTC is its first test.
  A rejected key now exits 2 rather than silently publishing a dataset with
  none of T19's or T20's corrections applied.

### Found by the coverage report, and not fixed

Both surfaced on 2026-09-03 by the first live ETF probe, and neither is in
scope for the change that found them. Raised rather than acted on.

- **A negative weight fails the schema, and 11 of the 49 EDGAR-sourced funds
  hit it.** N-PORT reports short positions and negative-value derivatives, so a
  holding can carry a negative `valUSD`; `weight` is constrained to `>= 0`, and
  renormalizing over a total that includes negatives also pushes a positive
  bucket past 1. XLK, XLE, XLY, XLP, VOO, VTI, VEA, VWO, VXUS, VTV and SH all
  build a record and then fail to validate. Most are rounding-scale
  (`-6e-06`), but `SH` -- an inverse fund -- is `-0.239799`, which is real
  exposure the schema has no way to express. Deciding whether the dataset
  represents a short position, or excludes the funds that hold one, settles
  what it publishes.
- **`build.py --no-stocks` silently produces 100% `Unknown` sector weights.**
  The enrichment index comes from `_index_stocks(stocks)` and `stocks` is empty
  under that flag, so every ETF record built without the stocks pass loses the
  sector axis entirely. The probe above shows `sector 100%` on all 38 records
  for exactly this reason. It is a trap rather than a defect in the output --
  no published record came from such a build -- but a refresh must never use
  the flag.

The next code change belongs to Phase 2 as well. See `ROADMAP.md`.

### Found by the client-integration review, and not fixed

Measured 2026-09-03 against the published `v1/` tree while scoping **W4**. All
six are listing metadata, vocabulary, or an unfilled field rather than
coverage, and none is in scope for the review that found them. Raised rather than acted on. They matter
more than their size suggests, because W4 would feed every one of them into the
client's asset rows, and **P10C** -- the client package they would land in --
exists on the finding that a wrong MIC is worse than an absent one.

**The first four are fixed in the pipeline by T23, 2026-09-03**, and are kept
here because their measurements are the before-picture. They are one defect
with four faces and one fix. `v1/` still holds all four until a rebuild.

- ~~**`XNAS` is never emitted.**~~ All 44,663 US listings were published as
  `XNYS`, Apple's own record included, so every Nasdaq-listed company claimed
  the NYSE. `config/exchange_mic.yml` mapped `""` to `XNYS` as the bare-symbol
  default, and the refinement its own third line promised -- "the build pass
  will override based on the source's listed exchange when known" -- was never
  written. **T23 wrote it, from the source's `mic` column rather than its
  `exchange` one: 8,236 listings move to `XNAS`.**
- ~~**`.DU` resolves to Dubai.**~~ `config/exchange_mic.yml` mapped it to
  `DIFX`; Yahoo's `.DU` is Duesseldorf, `XDUS`. 3,467 listings were published
  as Dubai in AED, and `APC.DU` is Apple. **Corrected in the map, and the same
  3,467 move to `XDUS`/`EUR`.**
- ~~**19,401 of 111,535 listings, 17.4%, carry a suffix the map does not
  have.**~~ `_resolve_mic_for_symbol` fell through to the `""` default and
  published `XNYS`/`USD` for a venue that was neither. 23 distinct suffixes;
  four German ones were most of the volume -- `.BE` 7,662, `.MU` 6,075, `.HM`
  1,276, `.HA` 839 -- and the tail includes `.IL` the LSE international order
  book, `.TWO` TPEx and `.AQ` Aquis. **The source answers 19,407 of the 19,769
  symbols on an unmapped suffix, so this is retired by reading it rather than
  by extending the map.** Its closing proposal -- that an unmapped suffix be a
  build error -- was **considered and rejected**: with the source answering
  98.2% it buys little, and it would fail the unattended Sunday refresh
  whenever FinanceDatabase adds a venue. The default is gone instead, so those
  listings publish no MIC.
  - **One entry in that tail was wrong, and it is the useful part of this
    bullet.** It reads `.TA` as Tel Aviv. The suffix actually carrying the
    Tel Aviv-looking rows is **`.TI`**, and it is *not* Tel Aviv: all 345 of
    its rows report `exchange: TLO`, and they are Snap, GoPro, Covestro,
    Glencore, Adidas and Air France KLM -- US and western European companies,
    quoted in EUR, domiciled across FR, DE, US, ES and NL, with no Israeli
    company among them. Most likely the Italian MTF EuroTLX. It is left
    unmapped rather than guessed, since mapping it on the strength of the code
    would have published 345 European blue chips as Israeli. Naming that venue
    properly needs the MIC registry in the candidates section below.
- ~~**`currency` is inferred from the guessed MIC and never read from the
  source.**~~ It derived the MIC from the symbol suffix and the currency from
  that MIC, so each of the three above was one error told twice.
  **`normalize_stock` now reads both, and 25,218 listings change currency**,
  led by `USD` to `EUR` 16,309 and `AED` to `EUR` 3,441.
  - Worth carrying forward, because it is what the fix does *not* reach:
    **369 rows name a venue but still get no currency**, because they resolve
    to one of 12 MICs the fallback table has no entry for -- `BVCA` 110,
    `XBER` 63, `XTAE` 61, `XJPX` 57, `XCOL` 20. The source leaves `currency`
    blank on 1,367 rows that do carry a `mic`, and the table is what answers
    for them. Raised, not fixed.
- **The sector mapping is a partial no-op, and a licence decision rests on
  it.** `config/sector_taxonomy.yml` renames eleven FinanceDatabase sector
  strings, and two of the eleven values actually published -- `Information
  Technology`, 9,266 records, and `Health Care`, 8,963 -- are not producible by
  that table, so they are unmapped pass-throughs. `industry_groups` is `{}` by
  design and `industry` is never mapped at all, so all 24 industry groups and
  every industry string pass through verbatim. The 2026-05-09 decision *Use
  generic sector labels and never name a proprietary taxonomy* is therefore
  satisfied in the documentation and only partly in the data. What limits the
  exposure, and belongs next to it: FinanceDatabase states its own
  categorisation is "a loose approximation of GICS" built "without collecting
  any actual data from MSCI's proprietary sources", so what passes through is
  the naming rather than the content.
- **`expense_ratio` and `inception_date` are schema fields no record carries.**
  0 of 49. `normalize.py:426,428` read both from the ETF metadata and the
  source supplies neither, so the schema advertises coverage the pipeline has
  no way to produce. They are the two most useful *unpriced* fund figures a
  tracker wants, and the client has no other source for either -- an expense
  ratio is not in a quote feed. For a US fund both are in the prospectus and
  in N-CEN rather than in N-PORT, so this is a new source rather than a new
  field. Either fill them or drop them from the schema; advertising an empty
  field costs a consumer a branch that never runs.

- [ ] **P1.** Get `validate-pr.yml` to run on fork pull requests.
  - Scope: a maintainer action, not a code change. Approve the pending workflow
    runs on #1, #2, #3, #5, #6, #7, and #8, and decide whether first-time fork
    contributors should stay gated. Nothing here needs a commit.
  - Acceptance criteria: `gh pr checks` reports a real result, pass or fail, on
    all seven open PRs.
  - Automated validation: the workflow itself, once it is allowed to start.
  - Manual validation: none.
  - Dependencies or blockers: **effectively blocked.** It needs repository write
    access on `wealthfolio/asset-profiles`, cannot be done from a fork, and the
    maintainer has since said the repository is on standby. Left on the page
    because it is still the right first action if that changes, not because it
    is expected.
  - Why first, if it happens at all: six changes are waiting on a check that has
    never executed. The cost is a button; the cost of not doing it is that every
    merge decision below is made on review alone.

- [~] **P2.** Land the FinanceDatabase URL fix and restart the refresh.
  **The fix half is done: #1 is merged into `main` at `ccab4c6f78`, 2026-09-03.
  The refresh half stays blocked on a maintainer.**
  - Scope: merge #1, then re-enable the schedule. Two separate causes stopped
    the weekly job and fixing one does not fix the other -- which is why half of
    this task could be closed and half cannot.
  - Acceptance criteria: a refresh run completes with conclusion `success` and
    commits; `v1/index.json` `generated_at` moves off 2026-05-31.
  - Automated validation: the refresh workflow's own run.
  - Manual validation: fetch `index.json` from jsDelivr and confirm the date
    moved.
  - Dependencies or blockers: **no longer blocked, as of 2026-09-03.** The
    schedule that matters is this fork's, not upstream's -- see the publishing
    decision in `DECISIONS.md`. Both this fork's workflows report `state:
    active` and neither has ever run. What the refresh now needs is
    `SEC_USER_AGENT` set as a repository secret, and sign-off on the rebuild,
    which is a 98,000-file rewrite that also removes roughly 8,000 shard URLs.
    Upstream's schedule stays stopped and that is no longer this project's
    problem.
  - **Delivered, and verified against the live source rather than on review.**
    `database/equities.csv` still answers 404 on 2026-09-03; both
    `compression/equities.bz2` and `compression/etfs.bz2` answer 200.
    `build.py --limit 500 --no-etfs --out <probe>` then fetched and parsed
    **112,654 equity rows** from the archive, normalized 500 records, and
    reported 500 valid and 0 invalid; `validate.py` on that probe exits 0 and
    the suite stays at 71 passed. **This is the first run of the stocks pass
    against the live source in this project** -- every earlier probe, T6's
    included, had to substitute for it.
  - Consequence for T5, and it is new: upstream now publishes 112,654 equity
    rows against the 98,464 stock shards in `v1/`. A rebuild is not a refresh of
    the same records, it is roughly a 14% larger dataset. Re-measure rather than
    plan against `v1/`'s counts.
  - Not covered by the above: the ETF pass. It needs `SEC_USER_AGENT` and a live
    EDGAR fetch, and `--limit` does not reach it, so #1's `etfs.bz2` half is
    verified as a URL and a parse but not through a full ETF build.
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

- [x] **T2.** Escape DOS device names in shard filenames.
  **Merged into `main` at `131deaab0a`, 2026-09-02, with the two debts below
  paid in the same commit. Still open upstream as
  [#5](https://github.com/wealthfolio/asset-profiles/pull/5), which is on
  standby -- so the branch stays as it is and the follow-up work lives on
  `main`.**
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
  - **Both debts below are paid, in the merge commit.** The two
    `xfail(strict=True)` cases became unexpected passes the moment the escaping
    landed, exactly as predicted, and are now plain assertions on the expected
    key. The missing coverage is written: the escape is asserted per device name
    and case-insensitively, `CONE`, `COM`, `COM10` and `ICON` are asserted
    unchanged because escaping them would break a working path for nothing, and
    `validate_shard_names` is checked on a filename, on a directory component,
    and through `validate_tree` so it cannot become a function nothing calls.
    The suite went from 37 passed and 7 xfailed to 61 and 5.
  - The merge also removed a second walk: `validate_shard_names` arrived with
    its own `rglob` beside T4's `shard_paths` and auto-merged without conflict,
    because the two never touch the same line. It now shares the one walk.
  - Owed on merge, and larger than that flip -- **now paid**: #5's stated test
    coverage was not in the tree. Its description reports 16 `shard_key` cases and a
    `validate_shard_names` fixture, but its diff adds no test file, so nothing
    re-runs any of it. #7 gives them a home, so committing them alongside the
    xfail flip is what makes the claim in #5's description true. This matters
    more here than elsewhere: 83,764 of 98,489 shards take their filename
    straight from an upstream ticker refreshed weekly, so the next `PRN` or
    `COM1` listing is a data event rather than a code change.
  - **Manual validation owed on merge: done, and it passes.** Cloned `main` on
    Windows 2026-09-02 with `core.protectNTFS` left at its default. The clone
    completed, `git status` was clean, nothing carried `skip-worktree`, and all
    98,464 stock shards were on disk -- the Linux count. `validate.py v1/` in
    that fresh clone reported the same 15 errors as Linux, and the suite the
    same 61 passed and 5 xfailed. This is the check the CI runner cannot
    perform, and it is the one that proves the defect is gone.
  - Also measured, and it corrects the diagnosis rather than the fix: **it was
    git that refused these names, not Windows.** `core.protectNTFS` rejects the
    path; Windows 11 on this host creates `CON.json` without complaint. The fix
    is still right, because git is what every contributor goes through, but
    `AGENTS.md` no longer claims the OS refuses it.
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

- [x] **T6.** Stop a path separator in a key creating an unreachable shard.
  **Done 2026-09-03, committed on `main` at `400678da69`.**
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
  - Dependencies or blockers: none, once #5 was merged into `main`. The escape
    character and the measurement that rules out the obvious alternative are the
    2026-09-02 `DECISIONS.md` entry, promoted out of `PLAN.md` when T4 took it
    over.
  - Delivered: `shard_key` joins its escaped components with `_` instead of
    `/`, so it always returns one filename component. `BRK/A` becomes `BRK_A`;
    `CON/A` becomes `CON__A`, because #5's per-component escape runs first and
    the two rules share a character. `build.py`'s two near-identical write loops
    became one `write_records`, which is where the collision guard lives: a key
    already written is reported and the record skipped, rather than the second
    silently replacing the first.
  - **Acceptance criteria, met and measured against the real dataset rather
    than a fixture.** Recomputing `shard_key` for all 98,474 records on disk:
    98,474 keys unchanged, exactly the 13 nested ones repaired, and **zero flat
    keys moved.** That is the criterion that matters, because every key is a URL
    a client may hold.
  - Automated validation: 71 passed, 0 xfailed, from 61 and 5. **No strict
    markers remain in the suite.** The five separator cases became unexpected
    passes the moment the fix landed and are now plain assertions on the exact
    expected key, and `CON/A` is asserted to compose to `CON__A` -- the
    regression the merge ordering existed to prevent. `scripts/tests/
    test_build.py` is new, guarded by `importorskip("pandas")` so the suite
    still runs on a bare install, and covers the collision, an invalid record
    never reaching disk, and the reap of a shard the old key nested.
  - **Manual validation: substituted, and say so.** The `--limit 2000` build
    cannot run -- FinanceDatabase moved its CSVs and #1, which repoints them, is
    not merged, so it dies on the same 404 that has failed every scheduled
    refresh since 2026-06-07. Ran the equivalent without the network: 2,013 real
    records including all 13 nested ones through `write_records` and
    `build_index` into a probe tree. No directory under `stocks/` or `etfs/`,
    `BRK_A.json` flat and named by the index, and `validate.py` on that tree
    **exits 0** -- the first tree in this project that passes the whole gate.
    What that does not cover is a real FinanceDatabase pull, so it proves the
    key repair and not the fetch.
  - `v1/` is untouched and still reports 15 errors. A code fix does not rewrite
    committed data; that is T5, and the probe above is the evidence that T5 would
    now produce a clean tree.
  - Evidence: 9 directories holding 13 records exist under `v1/stocks/`
    (`AKO`, `BF`, `BIO`, `BRK`, `CRD`, `HEI`, `HVT`, `RAC`, `WSO`). All 13 are
    committed, none is referenced by `index.json`, and none is schema-validated.
    Eleven of the 13 duplicate a dash-form shard that already publishes
    correctly, such as `BRK-A.json`; only `BIO/B` and `RAC/WS` have no
    alternate form. #5's new `validate_shard_names` uses `rglob`, so it sees
    nested paths -- but only to check them for device names, not to validate
    them against the schema.

- [x] **T7 (Phase 2).** Resolve N-PORT filings by fund series.
  **Submitted as [#6](https://github.com/wealthfolio/asset-profiles/pull/6),
  2026-09-01, and merged into `main` at `52fdc78ce3`, 2026-09-03, with the
  tests it owed at `55db8b4e0b`. Still open upstream and still awaiting CI
  approval (P1) and review. **Closed 2026-09-03: the manual validation it was
  left open for has been run, against live EDGAR.**
  - Scope as submitted: resolve a ticker to its `(CIK, series ID)` through
    SEC's `company_tickers_mf.json`, then take the newest N-PORT carrying that
    series. Series lookup reads each filing's `-index-headers.html`, about 3 KB
    and carrying `SERIES-ID`, rather than its multi-megabyte `primary_doc.xml`.
    The scan is memoised per trust and capped. Single-fund trusts -- SPY, DIA,
    GLD, SLV -- keep the existing CIK-level path unchanged. Touches only
    `scripts/build.py` and `scripts/sources/edgar.py`.
  - Acceptance criteria: four funds sharing a trust produce four different
    records. This is Phase 2's headline exit criterion, arriving before Phase 1
    closes. **Met against fixture filings, not against EDGAR** -- see the two
    validation entries below, which is the whole distinction that matters here.
  - **Automated validation: 78 passed, from 71.** #6 shipped no tests, the same
    debt #5 arrived with, so seven were written on merge in a new
    `scripts/tests/test_edgar.py` and committed at `55db8b4e0b`. They run
    against a fake HTTP layer holding one trust that files for two funds --
    the shape the defect lives in -- and cover the series lookup's CIK padding
    and case, the two funds resolving to their own filings, the per-trust
    header scan resuming rather than restarting, a series that never filed
    being reported instead of given a sibling's filing, a configured CIK that
    does not file the series being overridden and logged, and an unreadable
    mapping degrading to the CIK-level answer. `importorskip("requests")`
    keeps the suite runnable on a bare install, as `test_build.py` does.
    - Red-then-green was measured on the defect rather than on the new API,
      because seven `AttributeError`s prove only that the code is new: against
      the pre-merge `edgar.py`, XLK and XLF both return the same filing --
      `2026-04-30`, holding `MSFT` -- and after it they return their own. The
      file was restored byte-identical afterwards.
    - What that does not cover: the parse of a real multi-megabyte N-PORT, and
      whether a real `-index-headers.html` matches `_SERIES_ID_RE`. The fixture
      header is written to the format, not captured from EDGAR.
  - **Manual validation: done 2026-09-03, against live EDGAR, and it passes.**
    Refetching the four Schwab funds with `SEC_USER_AGENT` set gives four
    different filings, each recognisably its own fund rather than merely
    different from the others:

    | Fund | Holdings | Top three | Countries |
    | --- | --- | --- | --- |
    | SCHD | 102 | QUALCOMM, Texas Instruments, UnitedHealth | 4 |
    | SCHB | 2,411 | NVIDIA, Apple, Microsoft | 17 |
    | SCHX | 751 | NVIDIA, Apple, Microsoft | 12 |
    | SCHF | 1,479 | Samsung, SK hynix, ASML | 32, 6 US holdings |

    All four are about 99% Equity, where the published records say 98% Fixed
    Income; SCHD's dividend names and SCHF's ex-US concentration are each
    what that fund is. This also proves the two things the fixtures could not:
    a real `-index-headers.html` matches `_SERIES_ID_RE`, and a real
    multi-megabyte N-PORT parses. The published records are still the
    byte-identical 2026-05-31 ones until a refresh runs.
  - Dependencies or blockers: observing the result in published data needs P2,
    since no refresh can currently complete. Merging it into `main` needed
    neither -- `main` is this fork's integration branch, and its one line of
    `build.py` auto-merged clean over T4's and T6's rewrite of that file.
  - It also supersedes the CIK question: deriving the filer from SEC's own
    mapping makes a wrong `cik:` in the config a logged warning rather than a
    silent wrong record, and it finds **19 of the 52 configured US CIKs are
    wrong** -- #3's four, independently confirmed, plus every Select Sector
    SPDR (config points at SPDR Series Trust `0001064642`; they file under
    Select Sector SPDR Trust `0001064641`), plus VIG, VNQ, VYM, EEM, IEMG,
    QQQM, RSP, SMH, BND, VEA, VWO and VXUS.

- [x] **T9 (Phase 2).** Reject a country code ISO 3166-1 never assigned.
  **Done 2026-09-03, committed on `main` at `790b45e584`.**
  - Scope: `edgar._classify_country` accepted any `[A-Z]{2}` and fell back to
    the code as its own display name, so `XX` -- what an N-PORT filer writes
    for a holding it does not place -- became a country named `XX`. Drop it at
    the source and add the existence rule to `validate_record`.
  - Acceptance criteria, met: no new record can carry one, and a record that
    does is an error at the top level and per `country_weights` entry.
  - **The gate is red on `v1/`, deliberately, and this is the third time that
    has been the design working.** `python scripts/validate.py v1/` reports
    **4 errors** and exits 1, on SCHD, SCHB, SCHX and SCHF -- the same four
    records, and the only ones in all 98,473 that carry an unassigned code.
    Only a rebuild repairs them; do not delete or regenerate a shard to clear
    it. Verified against live EDGAR that a rebuild does repair them: refetching
    all four gives 0 `XX` holdings.
  - Automated validation: 78 passed to 90. Six new tests, every one confirmed
    red against the previous code and green after. The other six added assert
    unchanged behaviour and pass both ways, which is what they are for.
  - Manual validation: the locale-strict form
    (`-X warn_default_encoding -W error::EncodingWarning`) reports the same
    four errors and no `EncodingWarning`.

- [x] **T10 (Phase 2).** Resolve a holding's sector through CUSIP.
  **Done 2026-09-03, committed on `main` at `b8806b695d`.**
  - Scope: `_enrich_holding` joined a holding to the stock dataset on ISIN then
    ticker. Add a CUSIP leg, after both, so no existing match changes.
  - Evidence, and it corrects the premise in `ROADMAP.md`: the ticker leg is
    nearly useless for an EDGAR fund. Of 4,857 live holdings across SPY, QQQM
    and the four Schwab funds, **4,845 carry an ISIN and exactly 1 carries a
    ticker** -- N-PORT does not report tickers. The narrow side is the stock
    index, where only 14,716 of 98,463 records carry an ISIN against 16,519
    carrying a CUSIP.
  - Acceptance criteria, met and measured against live filings: resolved sector
    weight moves SCHD 87.0% to 98.5%, SCHB 66.6% to 80.1%, SCHX 68.5% to 79.8%,
    SPY 69.0% to 79.6%, QQQM 66.3% to 76.8%, SCHF 56.9% to 59.4%.
  - Manual validation: end to end through `normalize_etf` with the stock shards
    on disk as the index, SCHD's `Unknown` sector weight falls **13.0% to 1.5%**
    and Energy corrects from 9.3% to 13.3%, having been undercounted by the
    holdings that resolved nowhere. That is the red-then-green that means
    something: the nine new tests assert the API, so against the previous
    signature they fail as `TypeError` rather than as a behaviour difference.
  - Automated validation: 90 passed to 99.

- [x] **T11 (Phase 2).** Report per-fund coverage from the build.
  **Done 2026-09-03, committed on `main` at `209ddb2343`.**
  - Scope: the build reported `etfs: N valid, M invalid`. Under that a universe
    entry could produce nothing without being named, and a record whose weights
    are 100% `Unknown` looked like one that carries signal.
  - Acceptance criteria, met: one line per universe entry, either its holdings
    count and unknown share per axis or the reason it has no record,
    distinguishing the four ways an entry can vanish -- the source raised, the
    record did not validate, nothing was found and nothing reported, and the
    entry has no ticker.
  - Automated validation: 99 passed to 105, one test per branch.
  - **Manual validation: a live ETF-only build, and it earned its place
    immediately.** 38 of 65 entries produced a record, against 10 published.
    It named the 11 that build and then fail to validate and the 16 that
    error, and both findings above the task list came out of reading it.
  - Note: that probe ran `--no-stocks`, so every record reports `sector 100%`
    unknown. That is the flag, not the funds -- see the second finding above.

- [x] **T12 (Phase 2).** Absorb an ISIN-less record whose every symbol is claimed.
  **Done 2026-09-03, committed on `main` at `d9bcbd11fd`. This answers the
  duplicate-record question.**
  - Scope: `build_index` keys `symbols` by symbol and the last writer wins, so
    a record whose every symbol another record also lists reaches the index by
    no route at all. That was `stocks/SAND.json`, the gap of one T4 traced.
  - **Measured against the live source, because `v1/` no longer shows it.**
    T5 retired that shard, so only a rebuild recreates the defect. Of 112,654
    equity rows, 111,537 normalize and 90,515 survive the merge, and exactly
    one is unreachable: `SAND`.
  - Acceptance criteria, met: after the fix the same live data yields 90,514
    records, **0 unreachable and 0 symbols claimed twice**. The count moves by
    exactly one, so nothing else was touched.
  - The rule absorbs only a record whose symbols are *all* claimed. One that
    keeps a symbol of its own is why `BIO/B` and `RAC/WS` exist, and dropping
    every ISIN-less duplicate would lose the only record of those securities.
  - The `BRK/A` pairs turned out not to be part of this. T6 keys them `BRK_A`,
    distinct from `BRK-A`, so both are reachable -- two upstream listings, not
    one record hiding another. The `TASKS.md` text that grouped them with
    `SAND` predates T6 and was wrong by the time it was read.
  - `ECC` stays as it is: two ISIN-less rows for Eagle Point Credit that key
    alike. `write_records` reports the collision and skips the second, which is
    the right place for it and loses nothing silently.
  - Automated validation: 105 passed to 110. Both absorption tests confirmed
    red before the change; the three regression tests pass either way.

- [x] **T13 (Phase 2).** Omit a weighted list that is mostly unresolved.
  **Done 2026-09-03, committed on `main` at `ebf634d73b`.**
  - Scope: `_enrich_holding` buckets what it cannot resolve as `Unknown`, or
    `Other` for asset class, and `_renormalized` scales the result to 1.0, so a
    list carrying no signal passes every check. Drop one whose synthetic share
    exceeds half, at the source and as a validator rule.
  - Threshold: **0.5, `majority` read literally rather than tuned.** The
    alternative measured was 0.25, which would omit 19 of 49 rather than 10 and
    would discard partial signal on SSO 46%, VEA 42%, SCHF 40%, IEFA 37%,
    EFA 34% and IWF 31%.
  - Acceptance criteria, met and measured against the 49 records rebuilt the
    same day: omits `sector_weights` on 10 and `asset_class_weights` on 1, and
    no `country_weights` list on any fund. The split is not arbitrary -- six
    bond funds at 99.9-100%, where an equity sector is meaningless rather than
    missing, and four ex-US equity funds at 51-82%, which is a real gap.
  - **Gate: `validate.py v1/` reports 11 errors and exits 1.** The rebuild at
    `383fec4aea` predates the rule, so the tree holds exactly what the rule
    rejects. A rebuild clears it and the errors name every record it changes.
  - Automated validation: 115 passed to 124. Nine new tests including the
    threshold boundary. One existing test changed rather than added:
    `test_an_absent_country_code_is_not_an_error` used the label `Unknown` at
    weight 1.0 to assert something unrelated and began failing for the wrong
    reason, so it now names a real country. That interaction is the reason a
    threshold on a magic label needs a test at the boundary.

- [x] **T14.** Rebuild `v1/` from the live sources.
  **Done 2026-09-03 with sign-off, committed on `main` at `383fec4aea`, on its
  own as `AGENTS.md` requires. 99,693 files changed.**
  - Scope: the first full rebuild since bootstrap and the first refresh since
    2026-05-31, making six pipeline commits visible in the data.
  - Rehearsed first, into a scratch tree, so nothing about it was a guess:
    `--out` to a temporary directory, gate run there, and every number below
    taken twice.
  - Acceptance criteria, met: `diff: +1219 / ~89343 / -9130`; 90,513 stock and
    49 ETF records; index 111,584 symbols and 9,400 ISINs;
    **`python scripts/validate.py v1/` OK, exit 0**, from 4 errors.
  - Manual validation, which is the check that matters: `SCHD` reads as its own
    fund. It was 98.0% Fixed Income carrying the whole trust's holdings; it is
    now **99.95% Equity, 102 holdings, led by QUALCOMM, Texas Instruments and
    UnitedHealth**, with Health Care 20.6% and Consumer Staples 18.5%. That is
    Phase 2's headline defect gone from the data rather than only from the code.
  - **The stock count falls by 7,950 and 8,730 index symbols stop resolving,
    and this was measured rather than assumed.** Every one of those 8,730 is
    absent from FinanceDatabase upstream too: checked against the 112,651
    symbols it publishes today, **zero** were still present, so none was dropped
    by this pipeline. The ISIN count falls 14,725 to 9,400 for the same reason.
  - Timing, for the next one: 5m48s to build and 59s to validate with a warm
    cache; the ETF pass costs about eleven minutes more cold. `git add -A v1/`
    then takes about two minutes and the commit thirty seconds.
  - `generated_at` moves to 2026-09-03 and `next_refresh_at` to 2026-09-10,
    spending P2's acceptance signal as intended. Those fields were deliberately
    frozen through T5 because repairing reachability is not a refresh; this is
    one.

- [x] **T16.** Rebuild `v1/` to apply the omit rule.
  **Done 2026-09-03 with sign-off, committed on `main` on its own. This closes
  Phase 2.**
  - Scope: T13's rule landed after T14's rebuild, so the tree held exactly what
    the rule rejects and the gate reported 11 errors. Apply it.
  - Acceptance criteria, met: `diff: +0 / ~90562 / -0` -- no record added or
    removed, every file changed only because `provenance.fetched_at` is stamped
    per build. Counts unchanged at 90,513 stocks and 49 ETFs.
    **`validate.py v1/` OK, exit 0**, from 11 errors.
  - Manual validation, and it is what shows the rule is selective rather than
    blunt: **the rule works per axis, not per record.** `BND` drops an equity
    sector breakdown that was 100% `Unknown` and keeps its 40-country and
    asset-class lists, which are real. `SH` drops sector and asset class and
    keeps country. `SCHD` keeps all three at 0.2% unresolved.
  - Timing: 5m59s to build, 66s to validate -- within seconds of T14's, so the
    figure in `AGENTS.md` is now confirmed twice rather than measured once.

- [x] **T17.** Fail loudly when no SEC contact address is configured.
  **Done 2026-09-03, committed on `main`.**
  - Scope: `SEC_USER_AGENT` became a repository secret when this fork took over
    publishing, and `http_cache.DEFAULT_UA` still named
    `opensource@wealthfolio.app`. So a blank or missing secret did not fail --
    it sent upstream's contact address, satisfied SEC, and the build succeeded.
    Raised during review of that commit rather than found by a test.
  - **The consequence was worse than misattribution, and it was traced rather
    than assumed.** `sources.edgar._ticker_index` catches `Exception` and
    degrades to an empty mapping with a warning, by design. So a bad secret
    would resolve no CIK, produce no ETF record, let `reap_removed` delete all
    49 shards already on disk, pass the validator on the remains because the
    counts stay consistent at zero, and let `git-auto-commit` push it. A
    misconfigured secret would have silently removed every ETF record from the
    published dataset.
  - Delivered in two parts, because the requirement has two halves:
    - `DEFAULT_UA` now carries **no email at all**, so it cannot satisfy SEC by
      construction. The check is `"@" in user_agent` for `sec.gov` hosts only,
      placed ahead of the robots.txt fetch, which is itself a request to the
      host.
    - `build.py` runs the same check up front when the ETF pass is enabled and
      exits 2. Five seconds instead of a five-minute stocks pass followed by a
      wrong dataset. `--no-etfs` is unaffected, since it needs no SEC contact.
  - Acceptance criteria, met and measured on all three paths: a full build with
    no secret and a cold cache exits **2** having written **0** files; a
    `--no-etfs --limit 20` build with no secret exits **0** and writes 21 files;
    a configured contact passes.
  - Red-then-green on the defect rather than the API: against the committed
    `http_cache.py`, `_user_agent()` with nothing set returns
    `'Wealthfolio asset-profiles bot (opensource@wealthfolio.app) ...'` and no
    guard exists. That is the behaviour the fix removes.
  - Automated validation: 124 passed to 139. A new `test_http_cache.py` covers
    the only HTTP path the pipeline has, including that a warm cache still
    reads without a contact (no traffic, so no requirement) and that
    `notsec.gov` is not treated as SEC.
  - **Raised and not fixed:** the broad `except Exception` in `edgar` means any
    sustained EDGAR outage has the same shape -- no records, a passing gate, a
    push. T17 closes the configuration route into it, not the outage route. A
    build that was asked for ETF records and produced none arguably should not
    exit 0, but that is a behaviour change with a judgement in it and it is not
    what this task was for.

- [x] **T22.** Rebuild `v1/` to apply the identity and type rules.
  **Done 2026-09-03 with sign-off, committed on `main` at `d7d84ed9f9`, on its
  own as `AGENTS.md` requires. 90,563 files changed. This is where T19's and
  T20's corrections stop being served.**
  - Scope: T19 and T20 landed as pipeline rules and the published tree still
    held both defects. Apply them. It is the third rebuild in a day and the
    first that *removes* published URLs.
  - Rehearsed first into a scratch tree, as T14 and T16 both were, and every
    number below was taken there before being taken again here. The rehearsal
    is what found the three items under "what it turned up" below, none of
    which was visible from the code.
  - Acceptance criteria, met: `diff: +322 / ~90240 / -322`; 90,513 stock and
    49 ETF records, unchanged; index 111,584 symbols and **9,078** ISINs, down
    322. **`python scripts/validate.py v1/` OK, exit 0**, and the suite 221
    passed either side.
  - Manual validation, the eight shards T19's and T20's criteria name:
    `stocks/CA18452Y1007.json` is **gone** and AAR Corp. is at
    `stocks/AIR.json` with `"isin": null`; Clean Air Metals is still at
    `stocks/CLRMF.json` and still ISIN-less, which is the deliberate branch;
    `stocks/AT0000741053.json` is gone and Eaton Vance is at
    `stocks/EVN.json`; `stocks/AT0000A2H326.json` reads `"kind": "debt"` with
    no sector and no industry group, against *Consumer Discretionary* before;
    `CA85207K1075` (Sprott Physical Silver Trust, an ETP) and `CA13780R1091`
    (Canoe EIT Income Fund, closed-end) read `"kind": "fund"` with no sector,
    in `v1/stocks/` as decided.
  - **322 URLs stop resolving and 322 start**, which is the cost signed off:
    a record that loses a wrong ISIN re-keys to its `primary_symbol`. Every
    one of the 322 new keys was checked for a collision against the published
    tree before the rebuild ran -- none, and no two records competing for one
    new key.
  - Timing, third measurement and the first with an OpenFIGI sweep in it:
    **5m13s to build** and 72s to validate with a warm cache, against 44m for
    the rehearsal whose sweep was cold. `.http_cache` held no OpenFIGI
    responses at all before today, so the 940-request unauthenticated sweep is
    what the difference is -- worth knowing for CI, which is always cold and
    has the key.
  - What it turned up, none of it caused by the rules and all of it recorded
    where it belongs: the **615/137** figure is an over-count by 44 (see T20),
    T19 **reaches ETF output** through the holdings join (see T19), and one
    record is silently dropped every build on a shard-key collision (see
    **T21**).

- [ ] **T15 (Phase 2 follow-on).** Bridge a holding's ISIN to a record the
  dataset already has. **On hold by decision, 2026-09-03: it waits for a
  source that carries TSMC's Taiwan line. Do not implement it with a
  per-holding alias.**
  - Why, and it is measured rather than assumed: T13 omits `sector_weights` on
    four ex-US equity funds, and the cause is **not missing sector data**. Of
    the unresolved weight across VWO, IEMG, EEM, VXUS, SCHF and VEA, **58.7%
    is holdings whose identifiers match no stock record** against **0.2% that
    match a record carrying no sector**. FinanceDatabase's sector coverage is
    96% of its ISIN-keyed records.
  - The companies are already in the dataset. Unmatched holdings by ISIN
    prefix against stock records held for that market: CN 6,189 against 5,992,
    IN 1,777 against 5,558, JP 1,137 against 5,110, TW 1,347 against 1,572,
    KR 754 against 1,784. `TR` is the exception at 441 against 0, a genuine
    coverage gap a bridge would not close.
  - The join fails because N-PORT reports ISIN and CUSIP and **never a ticker**
    -- 1 of 4,857 holdings measured -- while the stock dataset carries 9,400
    ISINs and 12,798 CUSIPs against **42,817 composite FIGIs**.
  - **The licence is verified and it clears, 2026-09-03.** OpenFIGI maps ISIN
    to composite FIGI, and FIGI identifiers carry a Bloomberg public-domain
    dedication with the MIT licence embedded in the OMG standard: *"FIGI
    Identifiers may be freely reproduced, distributed, transmitted, used,
    modified, built upon, or otherwise exploited by anyone for any purpose,
    commercial or non-commercial"*. No attribution clause, no non-commercial
    limit, no restriction on storing or republishing a mapping. It is
    identifier mapping rather than quotes, fundamentals or a proprietary
    taxonomy, so neither the 2026-05-09 Yahoo decision nor the taxonomy one
    reaches it. Unauthenticated limits are 25 requests a minute at 10 jobs
    each; `robots.txt` disallows only `/search`. GLEIF's ISIN-to-LEI file is
    CC0 but bridges only to a legal name, needing fuzzy matching, so it stays
    the second choice.
  - **Measured against full holdings, 2026-09-03, and the bridge alone does not
    meet the criteria below.** Live N-PORT for the four funds through this
    repository's own `http_cache`, every unresolved ISIN mapped through
    OpenFIGI -- 7,265 distinct ISINs in 727 requests -- joined on composite
    FIGI only. **3,351 of the 7,265, 46.1%, reach a record**, and 3,249 of
    those carry a sector. Shares are computed with `normalize`'s own
    `_enrich_holding` and `_aggregate_weights`, so the `now` column reproduces
    the published omission rather than estimating it. Synthetic sector share,
    as published then with the bridge:

    | fund | holdings | unresolved ISINs | now | with bridge | publishes? |
    | --- | --- | --- | --- | --- | --- |
    | VWO | 6,411 | 4,563 | 76.9% | **53.7%** | no |
    | VXUS | 8,878 | 6,960 | 50.8% | 23.7% | yes |
    | IEMG | 2,700 | 2,308 | 82.4% | 49.1% | yes, by 0.9pt |
    | EEM | 1,251 | 1,041 | 80.8% | 47.1% | yes |

  - **One holding decides it, and it is a coverage gap rather than an
    identifier one.** TSMC's Taiwan line `TW0002330008` is the largest residual
    in all four funds -- 14.5% of VWO, 13.8% of EEM, 11.8% of IEMG, 3.9% of
    VXUS -- and the dataset does not hold it. Only the NYSE ADR, `TSM` /
    `US8740391003`, which is a separate security with its own FIGI that
    OpenFIGI correctly declines to equate with the ordinary share. Map that one
    ISIN to the ADR's record and all four clear with margin instead of three by
    a hair: **VWO 39.6%, VXUS 19.9%, IEMG 37.3%, EEM 33.2%**. The ADR record
    carries sector `Information Technology` and `country_code` `TW`, so the
    substance is right even though the security is not the same one.
  - Two routes measured and rejected, so they are not tried again:
    - **Never join on the ticker OpenFIGI returns.** Roche's ISIN yields a
      ticker set whose bare symbols match `RHHVF` *and* `ROP` -- Roper
      Technologies. It would have booked Roche's weight into Roper's sector
      silently. Composite FIGI only.
    - **Excluding non-equity holdings from the sector denominator is worth 1 to
      3 points, not the 5 to 8 the cash weights suggest**, because the share is
      renormalized: VWO 53.7% to 51.6%, still omitted. Cash is 4.3% of VWO and
      7.9% of IEMG. Worth doing for its own sake, no help here.
  - Prerequisite in `http_cache`, which is small but real: it has no POST path,
    and OpenFIGI's mapping endpoint is POST. Its module docstring already
    claims the key is `sha256(method:url:body)` while `_cache_key` hashes no
    body, so the body has to enter the key when POST does.
  - Acceptance criteria: the four funds publish `sector_weights` again, meaning
    their synthetic share falls below T13's 0.5, without any record's existing
    sector changing. **On the measurement above this needs the bridge and
    TSMC's Taiwan line together**; the bridge alone leaves VWO omitted and IEMG
    inside a rounding error of the threshold.
  - Dependencies or blockers: the licensing question is answered, so nothing
    factual is outstanding. **Three decisions are, and none should be settled
    by whoever implements this:**
    1. **Adopt OpenFIGI at all?** It would be the fourth source and the first
       that supplies no data of its own, only a join. `DECISIONS.md` needs an
       entry either way, since a later reader will otherwise re-run the licence
       question this task already answered.
    2. **How is TSMC's Taiwan line fixed?** Mapping `TW0002330008` to the ADR
       record is one line and clears all four funds today, but it asserts an
       equivalence between two securities that OpenFIGI deliberately does not,
       and it is a per-holding patch. Adding the missing local listings is the
       Phase 3 answer, costs more, and fixes the class rather than the case.
       The measurement above does not choose between them.
    3. **What does `provenance` say for a record whose sector arrived through a
       mapping?** Every record names source, URL, fetch time and licence, and
       today an ETF record names EDGAR. The sector would now be reached via
       OpenFIGI via a FinanceDatabase record, and the rule that a record which
       cannot be attributed does not ship makes this a schema question rather
       than a comment.
  - Prerequisite regardless of the above: the POST path in `http_cache`.
    **Done 2026-09-03**, with the body hashed into the cache key, and OpenFIGI
    is adopted -- see `DECISIONS.md`. Decisions 2 and 3 above are still open,
    and 3 blocks anything shipping.
  - **Two corrections to the TSMC option, both measured 2026-09-03.** First,
    *"adding the missing local listings is the Phase 3 answer"* names work
    Phase 3 does not own: `ROADMAP.md`'s Phase 3 is fund coverage -- the
    non-US ETF universe and the issuer fallback -- and says nothing about
    stock listings. So that route currently belongs to no phase, which is a
    gap in the plan rather than a scheduled fix. Second, neither source
    available can supply it: `TW0002330008` appears **zero times** in
    FinanceDatabase and **zero times** in GLEIF's 9.2-million-row ISIN-to-LEI
    file. Choosing "add the local listing" therefore means finding a fourth
    source for it, not doing more of what is already here.
  - **Decision 2 is settled, 2026-09-03, and it is the slower route.** The
    owner chose to hold this task until a source that actually carries
    `TW0002330008` is found, rather than alias it to the NYSE ADR's record.
    Aliasing was one line and cleared all four funds today; it was rejected
    because it asserts an equivalence between two distinct securities that
    OpenFIGI deliberately declines, and an omission is documented and visible
    while an asserted equivalence is invisible to the consumer and quietly
    wrong. So VWO keeps no `sector_weights` and the reason is a coverage gap
    on the record, which is the outcome this project prefers. The same answer
    should be expected for any future per-holding alias or hand-patched
    identifier equivalence.
  - **Consequence: no phase owns finding that source.** As recorded above,
    `ROADMAP.md`'s Phase 3 is fund coverage and says nothing about stock
    listings, and neither source here carries the line. That gap in the plan
    is now what blocks this task, and it is the thing to raise before this
    task is picked up again.
  - **Decision 3 was re-read and is smaller than it looks, measured
    2026-09-03.** The question was what `provenance` says for a sector reached
    through a mapping. It already happens: `v1/etfs/SCHD.json` names only
    `SEC EDGAR N-PORT`, while its `Health Care` and `Consumer Staples` labels
    are filled by `normalize._enrich_holding` joining holdings against the
    stock dataset on ISIN, ticker, then CUSIP -- so a FinanceDatabase-derived
    axis already publishes under an EDGAR-only provenance block. OpenFIGI
    would add a fourth identifier leg to that existing three-leg join, not a
    new source of data.
  - **So decision 3 is a pre-existing under-attribution rather than something
    the bridge creates, and it is still open.** Worth knowing before it is
    settled: per-axis provenance would be cheap, not expensive -- three blocks
    across 49 ETF records -- and it buys a *consumer* nothing. Provenance
    exists here for takedown and audit (`docs/asset-profiles-spec.md:101`,
    `SPEC.md:150`), and none of W1 through W5 reads it; the client's recorded
    profile model has no provenance field at all. What is real is the audit
    gap: FinanceDatabase is MIT, which requires attribution, and repo-level
    attribution in `README.md` probably discharges the licence while the
    per-record trail stays incomplete. Since this task is held, nothing is
    blocked on answering it.

- [~] **T18.** Stop a cross-listed record being identified by its depositary
  receipt's ISIN. **Measured 2026-09-03; the count is below and the fix is
  still a decision.**
  - Found 2026-09-03 while probing T15's join, and it is a defect in published
    data rather than in the pipeline's logic. Two records read wrong today:
    Nestle is `v1/stocks/US6410694060.json` and Hon Hai Precision is
    `v1/stocks/US4380908057.json`. Both are `US` ISINs naming a depositary
    receipt; both records carry `country_code` `CH` and `TW`, list the local
    line (`NESN.SW`, `2317.TW`) among their cross-listings, and hold the
    receipt's CUSIP and composite FIGI rather than the share's. Hon Hai's is
    the plainer case: its `primary_symbol` is `HHPD.IL`, a London GDR, and its
    `name` reads *Hon Hai Precision Industry Co., Ltd. Sponsored GDR RegS*. So
    the record presents as the receipt throughout, not only in its key.
  - It compounds with the client-integration review's unmapped-suffix finding
    above. `HHPD.IL` is a London GDR and `.IL` is one of the 23 suffixes
    `config/exchange_mic.yml` does not carry, so that listing publishes as
    `XNYS`/`USD`. The record for a Taiwanese company is therefore keyed by a US
    receipt's ISIN, named as a GDR, and led by a London line presented as New
    York in dollars -- while the `2317.TW` listing beside it is correct at
    `XTAI`/`TWD`. Fixing the suffix map does not fix the key, and fixing the key
    does not fix the suffix map.
  - The cause is upstream, not in `group_cross_listings`. FinanceDatabase
    reports the receipt's ISIN against the local symbol, so both rows arrive
    carrying `US6410694060` and the merge is right to group them. **The local
    ISIN never enters the pipeline at all**, which is why no fix is available
    inside `normalize.py` as written.
  - Why it matters beyond tidiness: `DECISIONS.md` makes ISIN the canonical
    record key, and a consumer joining on it is handed a different security
    than the one the record describes -- a US receipt in place of a Swiss
    share, with a different currency, exchange and holder of record. It is also
    why N-PORT's ISIN leg finds nothing for these companies: the filing reports
    `CH0038863350` and the dataset holds `US6410694060`. Nestle survives that
    only because OpenFIGI's answer for the Swiss ISIN happens to include the
    receipt's composite FIGI among 180 rows; Hon Hai does not, and is one of
    T15's misses.
  - Scope, and the first step is a measurement rather than a change: count the
    records whose ISIN country prefix disagrees with their own `country_code`.
    That is machine-detectable across `v1/` and nobody has run it, so the
    extent is unknown and the two above are the only confirmed cases. Decide
    what to do only once the number is known -- it bears on whether this is a
    schema question (a record needs more than one ISIN) or a source question.
  - Acceptance criteria: the count exists and is recorded here with its date;
    and either the affected records identify the security they describe, or the
    reason they cannot is recorded against the source that reports it.
  - Automated validation: none for the measurement half, which changed no
    code -- the suite stayed at 139 passed and `validate.py v1/` at exit 0
    either side of it. A fix needs both, plus a case over `US6410694060`.
  - Manual validation, done 2026-09-03: read `v1/stocks/US6410694060.json` and
    `v1/stocks/US4380908057.json` against what FinanceDatabase reports for
    their symbols, and confirmed the local ISINs appear in neither the source
    nor GLEIF. A fix must re-check the same two shards.
  - Dependencies or blockers: none for the measurement, which is done. A fix
    probably needs a schema change, since one record legitimately covers
    several ISINs, and that is a decision rather than an edit.
  - **The count, measured 2026-09-03 against the published tree at
    `550ab5ed09`: 2,142.** Both criteria above are met, and the answer to the
    schema-or-source question is *source*, twice over and for two different
    reasons -- so this task's title now covers only part of what the count
    holds. See T19 for the other part.
  - **Most records have no ISIN to disagree with.** 81,157 of the 90,513 stock
    records carry none, so the mismatch is 2,142 of the **9,356** that do --
    **22.9%**. Upstream is the reason rather than the pipeline: only 30,429 of
    FinanceDatabase's 112,654 equity rows, 27.0%, carry an ISIN at all. Worth
    holding next to `DECISIONS.md` making ISIN the canonical record key: nine
    records in ten cannot be reached by that key.
  - **The pipeline introduces none of them.** For all 2,142, the record's
    `country_code` is one FinanceDatabase itself reports against that ISIN --
    checked row by row against the live source, 0 exceptions. 292 are ISINs the
    source labels with more than one country across its own rows, and the merge
    picks one of the source's own answers. So `group_cross_listings` is
    exonerated across the whole class, not just on Nestle and Hon Hai.
  - What the 2,142 is made of, by two independent cuts:

    | cut | count | reading |
    | --- | --- | --- |
    | prefix is an offshore incorporation domicile (KY, BM, LU, IE, ...) | 1,123 | legitimate: incorporated there, operating elsewhere |
    | residual, prefix is a real operating jurisdiction | 1,019 | the class worth looking at |
    | carries a venue in its own `country_code` | 1,110 | record spans the home market -- the Nestle and Hon Hai shape |
    | no venue in its own `country_code` | 1,032 | |
    | name announces a receipt (ADR/GDR/ADS/sponsored) | 101 | confirmed receipt keying, named as such |

    The venue cut uses a MIC-to-country table built for the 47 MICs present. It
    is a lower bound on home-market presence and not an upper one, because the
    23 unmapped suffixes and the bare-symbol default both land on `XNYS` -- see
    the client-integration findings above -- so a real home line can be
    mislabelled as New York but never the reverse.
  - **The receipt half cannot be fixed from this source, and that is the answer
    to the second acceptance criterion.** The local ISINs appear in
    FinanceDatabase **zero times**: `CH0038863350` (Nestle's Swiss line),
    `TW0002317005` (Hon Hai's Taiwan line), and -- bearing directly on T15 --
    `TW0002330008` (TSMC's Taiwan line). The source publishes only the
    receipt's ISIN, against every listing including the local one: all five Hon
    Hai rows carry `US4380908057`, `2317.TW` included, and all eight Nestle
    rows carry `US6410694060`, `NESN.SW` included. So no fix is available
    inside `normalize.py`, none inside this source, and T15's Phase 3 answer of
    "add the missing local listings" cannot come from FinanceDatabase either.
    A second identifier source, or a schema that lets one record carry several
    ISINs, is the whole option set.
  - **Decided 2026-09-03: add a second identifier source.** Recorded here
    rather than in `DECISIONS.md` because the follow-on measurement narrowed
    which source can do it, and the narrowing is the useful part.
  - **OpenFIGI, now adopted, cannot be that source, and this is checked rather
    than assumed.** Its v3 mapping response carries ten fields --
    `figi`, `compositeFIGI`, `shareClassFIGI`, `name`, `ticker`, `exchCode`,
    `marketSector`, `securityType`, `securityType2`, `securityDescription` --
    and **no ISIN among them**. It is a one-way ISIN-to-FIGI map, so it can say
    that `US6410694060` is Nestle and it cannot produce `CH0038863350`. It does
    settle T19, which is a different question, and it is worth being explicit
    that adopting it does not close this task.
  - **The candidate that could, and it is unverified**: GLEIF's ISIN-to-LEI
    file, inverted. T15 rejected GLEIF on the grounds that it "bridges only to
    a legal name, needing fuzzy matching", and that objection is right about
    the forward direction and wrong about this one -- ISIN to LEI to *every
    other ISIN sharing that LEI* is an exact join with no name matching
    anywhere in it, and the file is CC0. **What decides it is unmeasured**:
    whether a depositary receipt's ISIN maps to the issuer's LEI or to the
    depositary bank's. If the issuer's, the Nestle and Hon Hai cases resolve
    directly; if the bank's, GLEIF is no better than OpenFIGI here. One file
    and one lookup settles it, and nobody has run it.
  - **Run 2026-09-03. A receipt's ISIN maps to the issuer's LEI, so the
    mechanism works -- and coverage is why it still does not close this task.**
    GLEIF's `isin-lei-20260903T071508.zip`, 9,205,209 ISIN-to-LEI rows over
    98,721 LEIs, fetched through this repository's own `http_cache`
    (`mapping.gleif.org/robots.txt` carries an empty `Disallow:`, so nothing is
    excluded).
    - **Nestle resolves.** `US6410694060`, the ADR ISIN this dataset
      publishes, and `CH0038863350`, the Swiss ordinary it lacks, map to the
      *same* LEI `KY37LUS27QQX7BB93L28` -- confirmed against the LEI register
      as *NESTLE S.A.*, legal address CH, so it is the issuer's LEI and not the
      depositary bank's. That LEI carries seven ISINs, four CH and three US.
      The join is exact and needs no name matching anywhere in it.
    - **Hon Hai does not.** Neither `US4380908057` nor `TW0002317005` is in the
      file at all.
    - **Nor does TSMC, which matters to T15.** `US8740391003` reaches a LEI
      carrying two ISINs, both US; `TW0002330008` -- the single holding that
      decides whether VWO and IEMG publish `sector_weights` -- is absent.
    - **Across the 2,142: 777 reach a LEI, 1,365 are absent, and 176 gain an
      ISIN issued in the country the record claims.** So GLEIF closes 8.2% of
      the class, and the Taiwan cases it is most needed for are exactly the
      ones missing. Worth adopting for what it reaches; not the answer to this
      task.
  - **The extent is 445, measured 2026-09-03, and no longer a name heuristic.**
    Every one of the 9,356 published ISINs was put to OpenFIGI, which types the
    security each identifies: **407 ADR, 24 GDR, 6 Canadian DR**, plus Dutch
    certificates, NY registered shares and plain receipts -- **445 records
    keyed by a depositary receipt's ISIN**, against the 2 this task was raised
    for and the 101 a name check found. A floor rather than a ceiling, since
    OpenFIGI had no answer for 836 of the 9,356. Led by `country_code` CN 52,
    JP 50, DE 48, GB 29, US 27 -- and those US 27 are the shape nobody
    expected: `CA67080A1093` is NVIDIA, `CA64113H1029` Netflix,
    `CA93267X1006` Walmart, each keyed by its *Canadian* depositary receipt.

- [x] **T19.** Decide what to publish when the source attaches one company's
  ISIN to another company that shares its ticker. **Decided, implemented and
  applied to the published data 2026-09-03; the rule is on `main` and the
  rebuild that spends it is T22.**
  - **Found 2026-09-03 by T18's measurement, and it is the sharper half of what
    that measurement turned up.** T18 asks about depositary receipts, where the
    record at least describes the right company under the wrong security's
    identifier. This is the other thing inside the same 2,142: **164 published
    stock records are keyed by an ISIN that belongs to a different company
    entirely.**
  - The case to read first, verified end to end in the published tree:
    `v1/stocks/CA18452Y1007.json` is **AAR Corp.**, a US industrial, listed
    `AIR`. `CA18452Y1007` is **Clean Air Metals Inc.**, a Canadian materials
    company -- which the dataset also holds, at `v1/stocks/CLRMF.json`, keyed
    by symbol with `"isin": null`. So the ISIN resolves to the wrong company
    and its real owner is unreachable by it. Same shape: Helmerich & Payne at
    `CA4234071054` (Hello Pal International), MKS Instruments at
    `CA24380K3038` (DeepMarkit), Essex Property Trust at `AU0000096943`
    (Experience Co), Eaton Vance Municipal Income Trust at `AT0000741053`
    (EVN AG), Putnam Premier Income Trust at `AU000000PPT9` (Perpetual).
  - **The cause is upstream and it is a bare-ticker join.** FinanceDatabase
    reports `EVN` / `AT0000741053` / United States / NYQ / `Eaton Vance
    Municipal Income Trust` in one row, while EVN AG's own eight rows
    (`EVN.VI`, `EVN.DE`, `EVN.BE`, ...) carry no ISIN at all. The Austrian
    company's identifier has been attached to the US fund that shares the bare
    symbol. This is the same failure T15 already rejected a route over --
    *never join on the ticker*, where Roche's ISIN yielded bare tickers
    matching Roper Technologies -- except that here it is baked into the source
    before the pipeline sees it.
  - Why it outranks T18 in harm even though it is smaller: T18's records
    describe the right company, so a consumer gets Nestle under a receipt's
    ISIN. Here a consumer joining on `CA18452Y1007` is handed a different
    company, in a different country, in a different sector, and the company it
    asked for is published under a key it has no way to guess.
  - **164 was the bare-ticker detector's output; OpenFIGI cut it to 104
    confirmed, 2026-09-03.** Asked what each of those 164 ISINs actually is,
    OpenFIGI resolved 147 and **named a different company than the record in
    104** -- `CA18452Y1007` is CLEAN AIR METALS INC, `CA7800871021` is ROYAL
    BANK OF CANADA against a record reading Rayonier, `CA5394811015` is LOBLAW
    against Loews. 36 were false positives where OpenFIGI agreed with the
    record, 7 ambiguous, 17 unresolved. **104 is the confirmed count**; the
    detector's 164 should not be quoted.
  - Still a floor, because the detector only finds a collision where *both*
    sides survived into the dataset sharing a bare ticker. It found 209 pairs
    in all; the other 45 are the same company under a wrong `country_code` --
    CSR Limited published as Morocco, Sayona Mining as Canada -- a third,
    smaller defect that needs no schema question to fix.
  - **A route that looked exact and is not, recorded so it is not retried:**
    comparing each record's own `composite_figi` against the FIGIs OpenFIGI
    returns for its ISIN. It fires on **1,242** records and is *not* a
    wrong-ISIN detector -- in most of them the names agree exactly (`ALUMINA
    LTD` against `ALUMINA LTD`) and it is the FIGI that is stale or names
    another venue's composite. A useful internal-consistency check and a
    misleading identifier check.
  - Scope, and it is a decision before it is a change: choose between dropping
    the ISIN from a record that fails a plausibility check and keeping it with
    the record marked. Dropping it is cheap, reversible, and costs the 164
    records their canonical key while making their true owners reachable;
    keeping it publishes a join that is known to be wrong. Either way the check
    belongs in `validate.py` as a rule rather than in an override file, because
    83,764 shards take their identity from a weekly upstream refresh.
  - Acceptance criteria: no published record is keyed by an ISIN the same
    source attributes to a differently-named company; and whichever rule is
    chosen is asserted in `scripts/tests` over at least the AAR Corp and EVN
    cases, so a refresh cannot quietly reintroduce them.
  - Automated validation: `python -m pytest scripts/tests` over whichever rule
    is chosen, and `python scripts/validate.py v1/` if it lands in the
    validator, which is where it belongs. Neither can run until the rule
    exists.
  - Manual validation: read `v1/stocks/CA18452Y1007.json` and confirm it no
    longer claims Clean Air Metals' ISIN, and that `v1/stocks/CLRMF.json` --
    Clean Air Metals itself, published today with `"isin": null` -- is
    reachable by that ISIN or is deliberately still not. Repeat for the EVN AG
    and Eaton Vance pair.
  - Dependencies or blockers: none factual -- the measurement is done and
    reproducible. It needs the publish-or-drop decision, which is a product
    question rather than an edit, and it should be settled together with T18's
    since both are answers to "what does this dataset do when the source's
    identifier is wrong".
  - **Decided 2026-09-03: drop the ISIN.** A record that fails the check keeps
    its identity and re-keys to its `primary_symbol` through `shard_key`, so
    AAR Corp. moves from `stocks/CA18452Y1007.json` to `stocks/AIR.json`. The
    grounds are this project's own: a wrong join is worse than an absent one,
    which is what the client's P10C package rests on. The real owner is *not*
    moved to the freed key -- FinanceDatabase gives Clean Air Metals no ISIN
    either -- so it stays at `stocks/CLRMF.json`, which is the "deliberately
    still not" branch of the manual validation above.
  - **Implemented as two required signals**, in `build.figi_identity`: OpenFIGI
    names a different company, *and* the ISIN's country prefix is an assigned
    ISO country disagreeing with the record's own `country_code`. Either alone
    is too loose, measured against the shipped rule: **the name check alone
    fires on 888 records** -- most of them the notes and certificates, whose
    name differs from their issuer's legitimately -- and **the country check
    alone on 1,927**, of which the offshore incorporations are correct. **322
    fail both.** The 1,927 is lower than T18's 2,142 for a reason worth
    keeping: that count included prefixes like `XS`, a Eurobond, which name no
    jurisdiction and so disagree with every `country_code` vacuously.
  - **The extent is 322, not 104**, measured 2026-09-03 by typing all 9,400
    published ISINs rather than the 164 a bare-ticker detector had proposed.
    The detector's 164 and its 104 confirmed were both floors, as recorded. The
    322 include 87 records wearing a *fund's or a note's* ISIN, a shape neither
    earlier count could see: `Dave & Buster's Entertainment` under an iShares
    ETF's ISIN, `Camden National Corporation` under `AMUNDI CAC 40`, `Daimler
    AG` under an Erste certificate's.
  - **Ordering matters and cost a bug.** Typing before checking identity
    republished `LU0950674332` -- SeaChange International, a US software
    company -- as a `fund`, because the Luxembourg fund ISIN it wrongly carries
    types as one. Found by the probe build, not by the tests. Identity is
    checked first now, and the 478 Austrian certificates are still spared
    because their ISINs are Austrian exactly like the records carrying them.
  - **Precision is high and under 100%, which is stated rather than glossed.**
    A corporate rebrand whose new name shares no token with the old, in an
    offshore domicile, trips both signals: `Foxconn Interconnect Tech.` is now
    `FIT HON TENG LTD`, `WANdisco plc` is `CIRATA PLC`. Those lose a correct
    ISIN. So does a heavy abbreviation -- `Industrial & Commercial Bank of
    China` against `IND & COMM BK OF-UNSPON ADR`. A `difflib` ratio guard at
    0.83 clears the transliteration class (`ARGENS`/`ARGENX`,
    `STROER`/`STROEER`, `SURGUTNEFTEGAS`/`SURGUTNEFTEGAZ`,
    `ESSILORLUXOTTICA`/`ESSILORLUXOT`) and deliberately stops there, because
    each further guard costs true positives and tunes on single records.
  - **A route that looks exact and is contaminated, now checked in both
    directions.** Using composite FIGI to *exonerate* a flagged record fails
    for the same reason using it to detect one does: it agrees for 97 of the
    152 flagged records that carry one, including `ARCHER DANIELS MIDLAND`
    against `ADMIRAL GROUP PLC`. The record's `composite_figi` comes from the
    same FinanceDatabase row as its wrong ISIN. Do not retry it.
  - **This rule reaches ETF output, which nothing here recorded until the
    rebuild was rehearsed, 2026-09-03.** `normalize._enrich_holding` joins a
    fund's holdings against the stock dataset on ISIN, ticker, then CUSIP, so
    disowning an ISIN also removes a leg of that join. Four ex-US developed
    equity funds lose sector resolution as a result -- `EFA` 0.335 to 0.3658
    `Unknown`, `IEFA` 0.3736 to 0.4043, `SCHF` 0.398 to 0.4242, `VEA` 0.4209
    to 0.4448 -- and no other axis on any of the 49 records moves at all.
    **This is the axis becoming honest rather than degrading**: the weight was
    previously booked into whatever sector the mis-keyed record carried, which
    is the hazard T15 already refused a route over. But all four still publish,
    since T13 omits at 0.5, and it is worth knowing that `VEA` now sits 5.5
    points from losing its `sector_weights` for a reason that has nothing to do
    with `VEA`.
  - Automated validation, done: 221 passed. `test_build.py` asserts the
    two-signal rule over the AAR Corp and EVN cases the criteria name, the
    ordering over `LU0950674332`, and that a `XS` prefix -- a Eurobond, which
    names no jurisdiction -- can never be the second signal.
  - Manual validation, done 2026-09-03 against `v1/` after T22's rebuild:
    `v1/stocks/CA18452Y1007.json` is gone, AAR Corp. is at `v1/stocks/AIR.json`
    with `"isin": null`, and `CA18452Y1007` is absent from `index.json`'s ISIN
    map. Clean Air Metals is still at `v1/stocks/CLRMF.json` and still
    ISIN-less, which is the "deliberately still not" branch the criteria
    allowed for. The Eaton Vance pair behaves the same way:
    `stocks/AT0000741053.json` gone, `stocks/EVN.json` written.

- [x] **T20.** Stop publishing instruments that are not equities as stock
  records. **Decided, implemented and applied to the published data
  2026-09-03; the rule is on `main` and the rebuild that spends it is T22.**
  - **Found 2026-09-03 by the OpenFIGI sweep run for T18 and T19**, which typed
    every published ISIN and so answered a question nobody had asked: *is this
    even a share?* For a meaningful number of records it is not.
  - The counts, from the 8,520 ISINs OpenFIGI resolved: **445 `EURO-ZONE`**,
    **108 `ETP`**, **49 `Closed-End Fund`**, **20 `Open-End Fund`**, **12
    `EURO-DOLLAR`**, **10 `EURO MTN`**, **9 `EURO NON-DOLLAR`**. Against 7,205
    `Common Stock`.
  - **The 445 are one issuer's structured certificates.** 443 records carry a
    name beginning `EGB OE` or `RCB OE` -- Erste Group Bank and Raiffeisen
    Centrobank turbo certificates -- and every one is `country_code` `AT`.
    `v1/stocks/AT0000A2H326.json` is published as `"kind": "stock"`, named
    `EGB OE TL.Z./DAIMLER`, with `sector` *Consumer Discretionary* and a single
    Vienna listing whose symbol is the ISIN itself. It is a leveraged
    certificate over Daimler, not a company, and it has no sector of its own to
    report.
  - Why it matters rather than being untidy: a client classifying a holding
    gets a sector and a country for something that has neither, and the
    certificates inherit the *underlying's* sector, so 443 Austrian records
    silently carry German industrial exposure. The ETPs are worse placed
    still -- this repository publishes funds under `v1/etfs/`, so an ETP in
    `v1/stocks/` is in the wrong tree as well as the wrong `kind`.
  - Scope: decide whether the stocks pass filters on instrument type, and if so
    what supplies the type. FinanceDatabase does not appear to carry one, so
    the cheap route is a name rule over the two `OE` prefixes, and the correct
    route is OpenFIGI's `securityType` -- now available, but it would make a
    third-party mapping a gate on what ships rather than an enrichment, which
    is a change in what OpenFIGI is for and needs `DECISIONS.md` to say so.
  - Acceptance criteria: the number of non-equity instruments published under
    `v1/stocks/` is stated and either zero or justified; whichever rule is
    chosen is asserted in `scripts/tests` over `AT0000A2H326`.
  - Automated validation: `python -m pytest scripts/tests` over the chosen
    rule, asserted on `AT0000A2H326` so a refresh cannot reintroduce the class,
    and `python scripts/validate.py v1/` if the rule becomes a gate.
  - Manual validation: read `v1/stocks/AT0000A2H326.json` and confirm it is
    either gone or no longer reports a sector it does not have; check one ETP
    and one closed-end fund the same way, since they need a different answer
    from the certificates -- a fund belongs under `v1/etfs/` rather than
    nowhere.
  - Dependencies or blockers: none factual. It shares T19's open question --
    what this dataset does when a source hands it something it should not
    publish -- and should be decided alongside it rather than separately.
  - **Decided 2026-09-03: keep the records, correct them.** They are retyped
    rather than filtered out, so no shard URL disappears and a client holding
    one learns what it is holding. `kind` grows from a const to
    `["stock", "fund", "debt"]` in `stock.schema.json`, and a retyped record
    **drops `sector`, `industry_group` and `industry`** -- the fields it had
    inherited from something it is not. `validate.py` routes all three kinds to
    the same schema, because a fund share or a note is the shape of a share
    with less filled in; only `v1/etfs/` needs a schema of its own, since only
    an ETF record carries holdings.
  - **The type comes from `securityType2`, not `securityType`.** Measured
    2026-09-03 over 8,564 resolved ISINs: **every FIGI row for a given ISIN
    agrees on `securityType2` -- 0 disagreements** -- while `securityType`
    splits one instrument across `EURO-ZONE`, `EURO-DOLLAR`, `EURO MTN` and
    `EURO NON-DOLLAR`. `marketSector` is unanimous too but cannot do the job
    alone: Bloomberg files fund shares under `Equity`, so the 93 funds need
    the finer axis. Anything not in the table defaults to `stock`, so a type
    OpenFIGI adds later leaves records exactly as they publish today.
  - **The count is 571, and 554 of them publish a sector they do not have.**
    478 `debt` (notes and structured certificates) and 93 `fund` (ETPs,
    closed-end, open-end). That is below the 622 this task was raised with,
    and the reason is T19 rather than a measurement error: 87 records that
    type as a fund or a note are equities wearing someone else's ISIN, and
    they are disowned instead of retyped. The two tasks partition the same
    sweep.
  - **615 was an over-count by exactly 44 and should not be quoted**, found
    2026-09-03 by rehearsing the rebuild rather than by re-reading the code.
    The sweep behind it took the *index's* 9,400 ISINs, which are the 9,356
    stock records carrying one **plus the 44 ETF records that carry one**.
    Those 44 type as `fund` because they are funds, and they live in
    `v1/etfs/` where `kind` is already right, so no stock record was ever
    going to be retyped for them. The `debt` half was unaffected and 478 is
    exact. The build's own log line is the figure to trust -- it types what
    the records carry, not what the index lists -- and the arithmetic checks
    against the rebuilt index: 9,078 = 9,356 - 322 + 44.
  - **The funds stay in `v1/stocks/`**, which the chosen option flagged as
    arguable and is the coherent reading: nothing here has their holdings, so
    they cannot satisfy `etf.schema.json`, and `v1/etfs/` is the tree for
    records that carry holdings and weights. An honest `kind` in the tree they
    are already in beats a move to a tree they cannot be valid in.
  - **This widened what OpenFIGI is for, and `DECISIONS.md` says so.** The
    adoption entry had ruled that no published field may take its value from
    OpenFIGI. `kind` now does. The clause still holds for every field a client
    classifies on -- sector, industry, country, weights -- and the grounds for
    moving it are that refusing the value means publishing 554 wrong sectors to
    protect a rule whose purpose was to prevent exactly that.
  - Automated validation, done: 221 passed, including
    `AT0000A2H326` asserted end to end -- retyped to `debt`, sector and both
    industry fields gone, still reachable at the same shard -- and a case
    proving an unmapped or absent type restates nothing.
  - Manual validation, done 2026-09-03 against `v1/` after T22's rebuild:
    `v1/stocks/AT0000A2H326.json` reads `"kind": "debt"` with no `sector` and
    no `industry_group`, against *Consumer Discretionary* / *Automobiles &
    Components* before. The criteria also asked for an ETP and a closed-end
    fund, since those need a different answer from the certificates:
    `CA85207K1075` (Sprott Physical Silver Trust) and `CA13780R1091` (Canoe
    EIT Income Fund) both read `"kind": "fund"` with no sector, and both stay
    in `v1/stocks/` as decided. Not one of the 571 retyped records kept a
    sector -- checked across the whole tree, not sampled.

- [ ] **T21.** Decide what happens when two records claim one shard key.
  **Found 2026-09-03 while rehearsing T19's and T20's rebuild; it is
  pre-existing and neither rule causes it.**
  - Every build logs `stock ECC: shard key 'ECC' is already written; skipping
    this record` and writes 90,513 records out of the 90,514 the cross-listing
    merge produced. The published tree has the same counts, so this is
    happening in what is served today and the rebuild neither introduced nor
    fixed it.
  - **The two records are the same company**, measured against the live source:
    `Eagle Point Credit Company Inc.` and `Eagle Point Credit Company Inc.
    Common Stock`, both `country_code` `US`, both sector `Financials`, both
    with a single listing `ECC`, and **neither carrying an ISIN**. They do not
    merge because `group_cross_listings` groups on ISIN, so two ISIN-less rows
    for one company stay separate, and then both compute `shard_key` `ECC`.
    It is exactly one collision in 90,514 records -- counted, not sampled.
  - **So nothing is mis-served today, and that is the reason this is a task
    rather than a defect.** The record that survives is a duplicate of the one
    dropped, and `stocks/ECC.json` reads correctly. What is wrong is the
    mechanism: the loser is decided by iteration order, the only trace is one
    log line among 470, and the build counts it as `invalid` when the record
    validates fine and merely lost a race. Two *different* companies colliding
    would be silently dropped the same way.
  - Scope: choose between merging ISIN-less records that share every listing
    symbol -- which is T12's rule for an ISIN-less duplicate, one step further
    -- and making a collision a build error. They are not exclusive: merging
    fixes this instance, erroring stops the next one being invisible.
  - Acceptance criteria: no build silently drops a record; either the pair
    merges, or the collision fails the build with both names in the message.
    Whichever is chosen is asserted in `scripts/tests` over the `ECC` pair.
  - Automated validation: `python -m pytest scripts/tests` over the new rule,
    and `python scripts/validate.py v1/`, which cannot see this today -- an
    unreachable shard is a validator failure since T4, but a record that was
    never written leaves nothing to be unreachable.
  - Manual validation: read `v1/stocks/ECC.json` and confirm which of the two
    names it carries, then rebuild and confirm the count reaches 90,514 or the
    build stops.
  - Dependencies or blockers: none. It is small, and it should not be bundled
    into a data rebuild, since fixing it changes the record count.

- [~] **T23.** Read a listing's venue and currency from the source.
  **Pipeline half done 2026-09-03, committed on `main` at `1530f70157`;
  `v1/` still holds all four defects until a rebuild, which needs sign-off.**
  - Scope: the first four findings of the client-integration review above,
    which are one defect with four faces -- the MIC was guessed from the Yahoo
    symbol suffix and the currency then derived from that guess, so each error
    was told twice.
  - **The source answers it directly, which the review did not know.** It ships
    a `mic` column, already ISO 10383, populated on **111,823 of 112,654 rows
    (99.3%)** across 72 well-formed values, and a `currency` column on 110,517.
    The review proposed reading `currency` and `exchange`; `exchange` is
    Yahoo's own code (`NMS`, `NYQ`, `IOB`) and would need a new code-to-MIC
    table, so `mic` is the smaller and better lever.
  - Acceptance criteria, met in the pipeline: the guess is no longer the
    primary answer, and `validate.py` passes on a full probe build.
    **47,310 of 112,654 rows disagreed with the source**; in the probe that is
    **47,285 of 111,535 listings, 42.4%**:

    | change | listings |
    | --- | --- |
    | `XNYS` to `OTCM` | 11,745 |
    | `XNYS` to `XNAS` | 8,236 |
    | `XNYS` to `XBER` | 7,662 |
    | `XNYS` to `XMUN` | 6,075 |
    | `DIFX` to `XDUS` | 3,467 |
    | `XTKS` to `XJPX` | 3,057 |
    | `XNYS` to `XTAE` | 527 |
    | `XNYS` to none | 406 |

    plus 25,218 currency corrections, led by `USD` to `EUR` 16,309 and `AED`
    to `EUR` 3,441. **`OTCM` was never counted by the review**: 11,745
    over-the-counter listings claimed the NYSE, more than the Nasdaq ones did.
  - Three changes to the suffix map, which stays as the fallback for the 831
    rows the source leaves: `.DU` corrected from `DIFX` to `XDUS`; the
    bare-symbol default `"": XNYS` retired, so a venue nobody can name is
    absent rather than wrong; and `.TI` deliberately left unmapped -- see the
    correction under the review findings above, which is the near-miss worth
    reading before touching this map again.
  - **`ILA` and `ZAC` are normalized to `ILS` and `ZAR`**, 969 rows, and
    `GBX` joins them. They are quoting units rather than ISO 4217 codes, and
    the grounds are that **this column cannot carry a quoting unit at all**,
    which is measured rather than argued: the vendor convention for these is
    mixed case -- `GBp`, `ZAc` -- and the column holds **no mixed-case value
    anywhere** among its 37, while `name` in the same rows is mixed case 88%
    of the time. Case was flattened upstream, so London's 1,890 `GBP` rows
    are ambiguous: a flattened `GBp` cannot be told from a real `GBP`. No
    consumer can read a unit off this field, so the only meaning it carries
    reliably is the currency.
    - An earlier version of this entry said the source "contradicts itself"
      by normalizing London while leaving the other two. That was too
      generous: `ZAc` arriving as `ZAC` shows the column was upper-cased, not
      normalized, so the London value is not a decision of the source's at
      all. Same fix, different reason, and the difference matters because the
      first reading implies the source knows London is pence and this one
      says nobody downstream can.
    - `GBX` is in the alias map because it would otherwise satisfy the
      schema's `^[A-Z]{3}$` and publish as though it were a currency. It
      appears 0 times today, so this is a guard rather than a correction.
    - The quoting unit is a real field this schema does not carry; the
      MIC-registry candidate below is where it belongs.
  - **A knock-on nobody predicted, and it is the reason this is not a
    one-line change.** `group_cross_listings` promotes a US-listed member of
    an ISIN group to primary by testing `exchange_mic` against a set of four
    US MICs. The old `""` to `XNYS` default made that test true for nearly
    every record, so the rule barely discriminated; with a real MIC it does.
    Measured against the probe: **1,997 records change `primary_symbol`** --
    Tyson Foods was led by `TF7A.BE`, a Berlin line, and is now `TSN` --
    **515 change `name`** toward the fuller US form (`CAESARS ENTMT INC.
    DL-,01` becomes `Caesars Entertainment, Inc.`), **149 change `sector`**
    and **71 `country_code`**, in each case because the source disagrees with
    itself between a company's listings and the US line is now preferred.
    This cannot be shipped separately: an accurate MIC is what makes the rule
    discriminate, so the two are one change.
  - **It also moves T19's count, by improving it.** The identity check
    compares OpenFIGI's name against the record's, and the record's name now
    comes from the US listing rather than a German one. 323 ISINs are dropped
    against 322, on a set that differs by 6 in and 5 out: `US4234031049` stops
    being disowned because the record now reads `Hello Group` rather than
    `Momo Inc.`, which is what OpenFIGI calls it.
  - Automated validation, done: **230 passed**, from 221. Nine cases over the
    source winning, the suffix fallback still running, an unmappable venue
    being absent, `.DU`, `.TI`, and the three currency forms.
  - Manual validation, outstanding until the rebuild: `v1/stocks/AAPL.json`
    still reads `XNYS` today. Verified instead against a full `--no-etfs`
    probe tree, where `validate.py` exits 0 and the record count is unchanged
    at 90,513.
  - Dependencies or blockers: none. The rebuild is the outstanding half, and
    it is much larger than T22's -- 47,285 listings and 1,997 primaries rather
    than 893 records.

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

- [x] **T4.** Make an unreachable or unvalidated shard a validator failure.
  **Done 2026-09-02, committed on `main` at `2ba50a5c83`. Branch
  `fix/unreachable-shard-validation` is cut off T3's branch and pushed to
  `origin`, holding only `validate.py` and `build.py`. No PR opened: upstream is
  on standby, so an eighth PR that turns the gate red by design and ships no
  tests would sit unread. It is ready to send if that changes.**
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
    more sit one level down. Three numbers, four values, and the validator
    reported only the one mismatch it happened to check.
  - **The gap of one is `stocks/SAND.json`**, identified as this task promised.
    It is a Sandstorm Gold record carrying no ISIN whose only listing symbol is
    `SAND`, and the same security also publishes as `stocks/CA80013R2063.json`,
    an ISIN-bearing record that merged seven cross-listings and lists `SAND`
    among them. `build_index` writes that symbol twice and the last writer won,
    so one record on disk reaches the index by no route at all. The root cause
    is `group_cross_listings` merging by ISIN only -- the same one that leaves
    `BRK/A` beside `BRK-A` -- so it is a duplicate-record question, not a
    counting one. Raised, not fixed: resolving it settles what the dataset
    publishes.
  - Delivered: `validate.shard_paths(directory)`, one sorted recursive walk used
    at four sites. `validate_tree` loops over it per kind, which collapses its
    two duplicated bodies into one and schema-validates nested records.
    `validate_index` collects the paths it already reads from `symbols` and
    `isins`, reports every file on disk that set does not name, and replaces the
    `counts` check with a three-way one printing all three numbers.
    `build.reap_removed` walks it and keys on the path below the directory
    rather than `path.stem` -- `BRK/A.json` is keyed `BRK/A` and stemmed `A`, so
    a recursive reap on the stem would delete every nested record. The re-read
    feeding `build_index` uses it too, so a record on disk becomes a record in
    the index.
  - Acceptance criteria, met: `python scripts/validate.py v1/` reports 17 errors
    on Windows and 15 on Linux, where it reported 3 and 0. Fourteen name a shard
    on disk the index does not name, including all 13 nested; one reports
    `counts.stocks=98464 but 98475 file(s) on disk and 98463 path(s) named`.
  - Automated validation: 37 passed and 7 xfailed, up from 32 and 7. Five new
    tests in `test_validate.py`, red-then-green checked: all five failed before
    the change. One of them passed at first for the wrong reason -- a one-level
    glob makes the count wrong by exactly one as well, so asserting on the error
    *count* accepted the old behavior -- and now asserts on the report naming
    the nested path. `conftest.py`'s `index_of` gained an `also` argument for
    indexes naming more than one shard.
  - Manual validation, both done: `build.py --no-stocks --no-etfs --out <dir>`
    over a probe tree holding `stocks/BRK/A.json` puts it in `index.json` under
    the symbol `BRK/A`, leaves the file in place, and the probe then validates
    clean -- so build and gate agree about a nested record. And `reap_removed`
    run directly over a fixture with a stale flat shard, a stale nested shard,
    and a current nested one reaped exactly the two stale ones.
  - Not covered, and disclosed: `reap_removed` and the re-read have no automated
    test. One has to `import build`, which pulls in `pandas`, `requests`, and
    `lxml`, and the suite is deliberately runnable with only `pycountry` and
    `jsonschema` -- which is what makes it work on a host where the full
    requirements do not install. See T8. The walk itself is covered at its three
    validator sites; its two build sites are covered by the probes above.
  - Also changed, and worth knowing: the re-read is now sorted, so which of two
    records claiming one symbol wins the index no longer depends on filesystem
    enumeration order. On the next rebuild that flips `SAND` to the ISIN-less
    record, because `CA80013R2063.json` sorts first. Deterministic and worse; it
    is the duplicate above that needs resolving, not the ordering.
  - **Consequence someone has to accept: this turns CI red on the committed
    data.** That is the change asking for a decision, not a defect in it. Green
    returns when T6 repairs the keys and T5 rebuilds, or sooner by deleting the
    14 orphans -- 14 files rather than T5's 98,000, and sign-off work either
    way. It was kept out of this change because `AGENTS.md` does not let a fix
    to a check delete the data the check found.

- [x] **T8.** Decide what to do about the numpy ceiling `etf-scraper` drags in.
  **Done 2026-09-03, committed on `main` at `908c1328d1`. Carried as an
  optional extra.**
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
  - **Decided: optional extra**, in `scripts/requirements-issuer.txt`. The
    deciding measurement is what the dependency earns rather than what it costs.
    All ten published ETF records carry `provenance.source` of `SEC EDGAR
    N-PORT`; none came from the scraper. So it capped every contributor's
    interpreter in exchange for a path that has produced nothing. Pinning the
    project to 3.12 would have been honest but paid that price for the same
    nothing, and replacing it with direct issuer fetches is Phase 3 work rather
    than a dependency tidy-up. The fallback is unchanged and still the
    documented route for non-US funds.
  - Acceptance criteria, met: `pip install -r scripts/requirements.txt` into a
    clean venv on **Python 3.14.5** succeeds, resolving numpy 2.5.2. The ceiling
    is confirmed still real and now isolated -- `pip install --only-binary=:all:
    -r scripts/requirements-issuer.txt` in that same venv fails on `No matching
    distribution found for numpy<2.0`.
  - Automated validation: 71 passed in that clean venv. `import build` succeeds
    without the package, and `fetch_issuer_holdings` raises a `RuntimeError`
    naming the optional file, which `build.py` already catches, records as a
    named ETF failure, and continues past. Nothing about what the dataset
    produces changes.
  - **Not verified, and it is the one risk left: the 3.12 install.** This host
    has only 3.14, so `refresh.yml`'s new second install step is reasoned from
    numpy 1.26 having a 3.12 wheel rather than run. A red first refresh run is
    the exposure, and the refresh is disabled anyway.
  - `validate-pr.yml` needed no change: it runs only the tests and the
    validator, so it simply stops installing a dependency it never used.
  - Branch: `chore/optional-issuer-extra` at `90695f5b82`, cut off
    `upstream/main` and pushed to `origin`. It holds the six files the change is
    about and nothing else, and its `issuer_scraper.py` and `refresh.yml` blobs
    are byte-identical to the gate-verified ones on `main`. No PR opened;
    upstream is on standby and `AGENTS.md` says to ask first.
  - **Building that branch turned up a live demonstration of why #5 matters.**
    `git checkout upstream/main` fails on this Windows host --
    `error: invalid path 'v1/stocks/CON.DE.json'` -- because upstream still
    carries the two unescaped shards. So the branch could not be made the normal
    way and was assembled with plumbing instead: `read-tree` of
    `upstream/main` into a temporary index under
    `-c core.protectNTFS=false`, six `hash-object` writes, `write-tree`, and
    `commit-tree`. The working tree was never touched and the repository
    config was not changed. Anyone cutting a branch from `upstream/main` on
    Windows will hit this until #5 merges; `main` itself checks out fine.

- [x] **T5.** Rebuild `v1/` with repaired keys and retire the nested shards.
  **Done 2026-09-03 by its minimal route, committed on `main` at `8122c95fdb`.
  Signed off as retire-and-reconcile rather than rebuild, so the 14 unreachable
  records are gone and `validate.py v1/` exits 0, but no record was
  regenerated and the published data is as stale as it was.**
  - Scope: one commit containing only regenerated data. T3, T4, and T6 are all
    on `main` now, so nothing is waiting on them. Delete the 9 nested directories and their 13 records, and
    `stocks/SAND.json`, which T4 identified as a fourteenth unreachable record
    and which a rebuild does not remove on its own -- `reap_removed` keeps it,
    because a current row still keys it. #5 already renames the two `CON` shards
    and their index entries, so those are not in scope here.
  - Acceptance criteria: `python scripts/validate.py v1/` exits 0 on Linux,
    macOS, and Windows from a fresh clone with no environment overrides -- which
    since T4 means every shard on disk is named by the index and the three
    quantities agree, not merely that every record parses; no directory remains
    under `v1/stocks/` or `v1/etfs/`; `git status` on a fresh Windows clone
    reports no missing files.
  - Automated validation: `validate.py v1/` in CI, and the T1 suite.
  - Manual validation: fresh `git clone` on Windows, then validate; spot-check
    that `BRK-A.json` and the repaired `BRK/A` record are not duplicates of each
    other.
  - Dependencies or blockers: **blocked on sign-off, and on that alone now.**
    This deletes tracked data and rewrites tens of thousands of files. Per
    `AGENTS.md`, that is destructive work and is not implied by the pipeline fix
    that requires it. Until 2026-09-03 it was also blocked on the source: the
    stocks pass died on a 404 and could not have rebuilt anything. #1's merge
    removed that half, so this is now a decision rather than a wait.
  - Scope grew with that merge, and the number should be re-measured before
    starting: upstream publishes 112,654 equity rows against `v1/`'s 98,464
    shards, so a rebuild adds roughly 14,000 records as well as repairing the
    13 nested keys. A cheaper alternative exists and is worth pricing against
    it -- delete the 14 unreachable shards and regenerate `index.json` alone
    with `build.py --no-stocks --no-etfs`, which is a 15-file diff rather than a
    98,000-file one, at the cost of leaving the published records as stale as
    they are today. **This is the route that was signed off and taken.** The
    full rebuild stays available and unstarted.
  - **Measured before deleting anything.** Simulating the rebuild over the
    surviving records put counts, files on disk, and distinct paths named all at
    98,463 stocks and 10 ETFs, with no `shard_key` collision, nothing on disk
    unnamed, and nothing named-but-missing. So the 15 errors were known to clear
    before a file was touched, rather than hoped to.
  - Acceptance criteria, met on the criteria this route can reach:
    `python scripts/validate.py v1/` **exits 0**, from 15 errors, and so does
    the locale-strict form with `-W error::EncodingWarning`. No directory
    remains under `v1/stocks/` or `v1/etfs/`. 71 passed. The fresh-Windows-clone
    check is unchanged and still passing, since #5 already fixed what broke it.
  - **`index.json` changed by one line** -- `counts.stocks` 98464 to 98463 --
    which is T4's diagnosis confirmed rather than merely applied. All 14 were
    unreachable by every route, so removing them moved no symbol and no ISIN.
  - **`generated_at` and `next_refresh_at` were deliberately held at
    2026-05-31 and 2026-06-07.** `build_index` stamps the current time, and
    `SPEC.md` is explicit that `next_refresh_at` is a commitment and a dataset
    past it is misreporting its own freshness. These records are still the ones
    built on 2026-05-31; repairing reachability is not a refresh and must not
    claim to be one. Restoring the two fields after the rebuild is the only
    hand-edit in the commit, and P2's acceptance signal -- `generated_at` moving
    off 2026-05-31 -- is therefore still unspent and still means what it meant.
  - What this route does **not** do, and it is the reason the full rebuild stays
    on the page: no record is regenerated, so every shard still holds data
    fetched on 2026-05-31, and the roughly 14,000 equity rows upstream has added
    since are still absent. `BIO/B` and `RAC/WS` had no dash-form alternate and
    are now simply absent rather than repaired, which the open duplicate-record
    question below covers.

### Measurements and questions owed Phase 1

- ~~Why `counts.stocks` exceeds the number of distinct index paths by one.~~
  **Answered 2026-09-02 by T4**: `stocks/SAND.json`, an ISIN-less duplicate of
  `stocks/CA80013R2063.json` whose only symbol the ISIN-bearing record claims in
  the index. Recorded under T4, and it opens a new question below.
- ~~Whether the weekly schedule is disabled.~~ **Answered 2026-09-02**: nine
  scheduled runs failed on a 404, 2026-06-07 to 2026-08-02, then no run at all.
  Both causes are named in P2.
- ~~What to do about a record duplicated across an ISIN-bearing and an
  ISIN-less row.~~ **Answered 2026-09-03 by T12**: absorb an ISIN-less record
  only when *every* symbol it lists is already claimed. Measured against the
  live source, that is exactly one record, `SAND`, and after the fix nothing is
  unreachable. The question assumed `SAND` and the eleven `BRK/A` pairs were
  one defect; they are not, because T6 keys `BRK/A` as `BRK_A` and both forms
  are reachable. `BIO/B` and `RAC/WS` are kept, since neither is shadowed.
- ~~Which repository publishes to the CDN.~~ **Answered 2026-09-03, twice.**
  First: neither, in any meaningful sense, upstream being on standby. Then
  **this fork does** -- decided the same day and recorded in `DECISIONS.md`.
  `README.md` points jsDelivr at `rwgs/asset-profiles@main`, the refresh
  workflow commits as the GitHub Actions bot and takes `SEC_USER_AGENT` from a
  repository secret, and the weekly refresh is this repository's obligation.
  Fetching the repointed URLs turned up three defects that predate the fork and
  are fixed in the same commit: `stocks/AAPL.json` and `etfs/SPY.json` 404
  because a record is keyed by ISIN, `@v1.0.0` names a tag that exists on
  neither repository, and the record counts were aspirational.
- **`SEC_USER_AGENT` is not yet set as a repository secret on
  `rwgs/asset-profiles`**, and the ETF pass takes 403 from EDGAR without it.
  `gh secret list` reports none. That is the one thing standing between the
  workflow as committed and a refresh that completes.

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

- [ ] **W8.** Publish an index a desktop client can actually fetch.
  - Scope: `v1/index.json` is **11.2 MB** and the tree behind it is 376 MB
    across 90,513 shards, so today the cheapest possible lookup costs 11 MB
    over the wire and W4's 1-day index TTL means paying it weekly. Options are
    a prefix-sharded index, a compact line-oriented form, or a symbol-to-shard
    map stripped of the ISIN mirror; the choice is the task.
  - Acceptance criteria: resolving one symbol costs a bounded, small fetch, and
    the client can tell a cached index is still current without downloading it.
  - Dependencies or blockers: none. Independent of Phase 3, and it changes a
    published artifact, so settle it before anything pins to the current shape.

- [ ] **W9.** Make `(ticker, MIC)` a first-class lookup key.
  - Scope: the client keys an asset by ticker plus MIC -- that is what
    `instrument_key` is -- while this index offers a Yahoo-suffixed symbol and
    an ISIN. So W4's resolution ladder has to round-trip a suffix back to a
    MIC, through exactly the map the findings section above shows is wrong for
    17.4% of listings. The measurement that scopes it: **9,356 of 90,513 stock
    records carry an ISIN**, so the identifier route covers 10% and the symbol
    route carries the rest.
  - Acceptance criteria: the index answers a `(ticker, MIC)` question directly,
    without the client re-deriving a venue from a Yahoo suffix.
  - Dependencies or blockers: the listing-metadata findings above. Fixing the
    key while the venues are wrong publishes the wrong join.

## Candidate additions, not scoped

Asked and answered on 2026-09-03 while scoping what the client actually needs
from this dataset. **Nothing here is scoped or committed**; it is recorded so
the reasoning is not re-derived, and because two entries are refusals whose
grounds matter more than the ideas themselves.

### Reference data, which both repositories need

- **An ISO 10383 MIC registry with quoting units.** Per MIC: name, operating
  versus segment, country, status, settlement currency, and the *quoting* unit
  -- `GBp`, `ILA`, `ZAc` -- which the current `^[A-Z]{3}$` currency pattern
  cannot express. This repository needs it to fix the listing findings above;
  the client needs it for **P10C** defects 15 and 16 and issues I8 and I9. One
  artifact, two consumers, and the smallest thing on this page.
- **An ISO 3166-1 to region table.** **W7** already owes the client the list of
  codes this dataset can emit; publishing the table costs little more and gives
  **W3** something to check against rather than guess.
- **Trading calendars per MIC**, derivable from `exchange_calendars`
  (Apache-2.0). Lets a consumer tell a market holiday from a missing quote.

### Coverage

- **Every US-registered fund, rather than 65 hand-picked ETFs.** N-PORT is
  filed by all registered investment companies, so mutual funds and closed-end
  funds are in reach of machinery that already exists: `company_tickers_mf.json`
  is 28,512 share classes and #6's series-level selection already reads them.
  It would retire `config/etf_universe.yml` as a hand-curated list, and it
  answers the client's `cef`, `oef` and `ut` broker codes -- its **I15** --
  with real records. The largest single lever on this page.
- **The share-class graph.** `VWRL`, `VWRP` and `VWCE` are one fund, and
  series-to-class gives it free for US funds. **W6** already flags that the
  client holds the accumulating class and the universe lists the other two.
- **Fund structure and tax attributes**: domicile, legal form, UCITS status,
  accumulating versus distributing, and UK **Reporting Fund Status**, which
  HMRC publishes as a register. Static, unpriced, and supplied by no quote
  feed, which makes it the most *distinctive* thing this dataset could carry.

### Metrics, and the decision that gates them

- **Shares outstanding, EPS and declared dividends per share**, from SEC XBRL
  `companyfacts` -- US-government public domain, roughly 8,000 filers,
  quarterly history to about 2009. The framing that matters: publish the
  unpriced half and let the client compute market cap, P/E and yield against
  its own quote, so no record here ever contains a price.
- **Blocked as written.** The 2026-05-09 decision *Never publish data derived
  from Yahoo Finance, or anything priced* puts fundamentals out of scope
  "regardless of source". It was aimed at Yahoo's terms and it catches
  public-domain SEC filings too. Either amend it to *nothing priced, and
  nothing whose source forbids redistribution*, or this whole subsection stays
  closed. The bullet above is the test case for where that line sits.

### Refused, with grounds

- **Risk metrics -- volatility, Sharpe, Sortino, beta.** Each is a function of
  a price series, so a published figure is a derivative of one, which the same
  2026-05-09 decision already forecloses -- "the stored derivative is still a
  derivative". There is also no free redistributable global end-of-day source
  to compute them from. And it would be the wrong answer even if both held: a
  published ratio is a fixed window in the fund's own currency, while the
  holder wants their own holding period and base currency. The client computes
  these locally from quotes it already stores; see `wealthfolio-dev` **P1A**.
- **A risk-free rate series per currency.** Genuinely public -- Treasury, ECB,
  Bank of England -- but the client already owns it as **P1F** and already
  fetches the US curve in `US_TREASURY_CALC`. Worth doing here only if the
  client would rather consume one normalised series than maintain three
  fetchers, which is its call and not this repository's.
- **Corporate actions.** Splits and ex-dividend dates are the thing the client
  most needs from a non-Yahoo source and there is no clean free one. XBRL gives
  declared dividends per share, not ex-dates or reliable split ratios. Better
  refused explicitly than left on a list looking possible.
- **Logos.** The client bundles 123 MB across 6,149 PNGs keyed by bare symbol,
  so a CDN set keyed properly would fix real misses and shrink its installer.
  They are trademarks, and carrying them would change this repository's licence
  story from "public-domain and MIT sources" to something needing its own
  defence.

### A risk already shipped

- **`cusip` appears in 15,808 published records.** CUSIP Global Services
  asserts rights in bulk redistribution of CUSIP numbers and has litigated
  them. That is a larger exposure than anything proposed above and it is
  already live, arriving from FinanceDatabase and from N-PORT. Settle it before
  **T15** adds identifiers rather than after.

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
