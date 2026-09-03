# No change in flight

Phase 2 closed on 2026-09-03, the day it opened. There is nothing mid-edit, and
saying so is more useful than leaving a finished plan in place pretending to be
current.

Everything that must outlive the last change has been promoted: the two
rebuilds and their measurements to `TASKS.md` under T14 and T16, Phase 2's exit
criteria to `ROADMAP.md`, the publishing decision to `DECISIONS.md`, and the
gate's new resting state to `AGENTS.md`.

## Where the project stands

`python scripts/validate.py v1/` **exits 0** against a dataset rebuilt the same
day, and the suite is **124 passed** (97 and 2 skipped on a bare install). The
published dataset is 90,513 stock records and 49 ETF records, generated
2026-09-03, with `next_refresh_at` 2026-09-10 -- a commitment this repository
now has to keep, since it is what jsDelivr serves.

Phase 2 existed for one sentence, and it is true now: **`SCHD` describes
`SCHD`.** It published 98.0% Fixed Income carrying the whole Schwab trust's
holdings for three months. It publishes 99.95% Equity, 102 holdings led by
QUALCOMM, Texas Instruments and UnitedHealth, Health Care 20.6% and Consumer
Staples 18.5%.

## What is worth doing next, in order

**T15, the identifier bridge**, is the highest-value work and `TASKS.md` has
it. It is the difference between a coverage gap and a correct answer among
T13's ten omissions: six are bond funds, where omitting an equity sector is
right, but IEMG, EEM, VWO and VXUS lose a list only because their holdings
cannot be joined. The measurement that makes this the right fix rather than a
new data source:

- 58.7% of unresolved weight is holdings matching no stock record; 0.2% is
  records carrying no sector.
- The companies are already here: CN 6,189 unmatched holdings against 5,992
  records held, IN 1,777 against 5,558, JP 1,137 against 5,110.
- N-PORT reports ISIN and CUSIP and never a ticker -- 1 in 4,857 holdings --
  while the dataset carries 9,400 ISINs and **42,817 composite FIGIs**.

Check OpenFIGI's licence before writing anything. `DECISIONS.md` constrains
this area, and identifier mapping not being quotes, fundamentals or a
proprietary taxonomy is an argument, not an answer.

**Then Phase 3.** `ROADMAP.md` has the order; it has not been opened and its
exit criteria have not been re-read against what the last two days changed.

## Two things to know before touching the pipeline

- **The first scheduled refresh has never run.** `SEC_USER_AGENT` was set as a
  repository secret on 2026-09-03 at 08:13Z, so the next Sunday 06:00 UTC run
  is the first end-to-end test of the workflow on a runner. It will rebuild and
  push `v1/**` unreviewed if it succeeds, and the gate runs before the commit
  step, so a red gate stops the push rather than publishing over it.
- **`build.py --no-stocks` silently omits every `sector_weights` list.** The
  enrichment index comes from the in-memory stocks pass, so an ETF-only build
  resolves nothing and T13's rule then drops the axis entirely. It is a trap
  rather than a defect in the output, and a refresh must never use the flag.

## Two upstream facts that have not changed

- Upstream is on standby and the seven open pull requests have still never been
  through CI. P1 needs write access nobody here has.
- Work still lands on `origin/main` and each change still keeps an
  upstream-mergeable branch. That this fork publishes does not change where
  changes are offered.
