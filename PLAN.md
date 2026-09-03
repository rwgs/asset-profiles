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
day, and the suite is **139 passed** (97 and 3 skipped on a bare install). The
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
it, now with the measurement it was waiting for. Two things are settled since
this section was last written, and one of them corrects it.

**Settled: the licence clears.** FIGI identifiers carry a Bloomberg
public-domain dedication with MIT embedded in the OMG standard -- freely
redistributable, commercial use allowed, no attribution clause, no restriction
on storing a mapping. It is identifier mapping rather than quotes,
fundamentals or a proprietary taxonomy, so neither 2026-05-09 decision reaches
it. Nothing needs re-checking here.

**Corrected: this is not purely a join problem.** The bridge resolves 3,351 of
7,265 unresolved ISINs across the four funds, which takes VXUS, IEMG and EEM
under T13's threshold but leaves **VWO at 53.7% and still omitted**, and IEMG
inside a rounding error of it. The deciding residual is a coverage gap after
all: TSMC's Taiwan line is the largest unresolved holding in all four funds and
the dataset holds only the NYSE ADR. Resolve that one ISIN as well and all four
clear with margin -- VWO 39.6%, VXUS 19.9%, IEMG 37.3%, EEM 33.2%. So T15 and
Phase 3 overlap where this section said they did not.

**What is actually blocking it is three decisions**, listed under T15 and
deliberately not taken while measuring: whether to adopt OpenFIGI as a fourth
source at all, whether TSMC is fixed by a mapping to the ADR record or by
adding the missing local listings in Phase 3, and what `provenance` says for a
record whose sector arrived through a third-party mapping. The last is the
sharpest, because a record that cannot be attributed does not ship.

Two smaller things the measurement produced, both recorded under T15 so they
are not rediscovered: never join on the ticker OpenFIGI returns, because
Roche's ISIN yields bare tickers matching Roper Technologies; and excluding
cash from the sector denominator is worth 1 to 3 points rather than the 5 to 8
the cash weights suggest, because the share is renormalized.

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
