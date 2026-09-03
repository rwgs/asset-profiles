# In flight: T23's rebuild. T19 and T20 are complete in code and in data

The arc that has been in flight since the OpenFIGI sweep is finished. Both
rules are on `main`, and **T22's rebuild applied them to `v1/`**, so the
defects they correct have stopped being served rather than only stopped being
produced.

**What is in flight is T23**, and it is in exactly the state T19 and T20 were
in this morning: the pipeline half is on `main` at `1530f70157` and gate-
verified, and `v1/` still holds the defect. A listing's venue and currency now
come from the source's own `mic` and `currency` columns rather than from a
guess at the symbol suffix. The rebuild that spends it is larger than T22's by
two orders of magnitude in records touched -- **47,285 of 111,535 listings,
42.4%, change their MIC**, 25,218 change currency, and 1,997 records change
`primary_symbol` as a knock-on -- so it wants its own sign-off and its own
rehearsal, both of which are done and recorded under T23.

**One thing to know before that rebuild runs unattended:** `refresh.yml` fires
Sunday 06:00 UTC, builds, validates and auto-commits `v1/**` as the bot. T23
is on `main` now, so if no rebuild happens first, that job is what publishes
these 47,285 corrections, with nobody reading the diff.

## What landed, and where it can be seen

**T19: a record keyed by another company's ISIN loses the ISIN** and re-keys to
its `primary_symbol`. Two independent signals are required, because either
alone is too loose: OpenFIGI names a different company, *and* the ISIN's
country prefix is an assigned ISO country that disagrees with the record's own
`country_code`. AAR Corp. is now `v1/stocks/AIR.json` with `"isin": null`, and
`v1/stocks/CA18452Y1007.json` -- Clean Air Metals' identifier -- is gone.

**T20: a record that is not an equity is retyped rather than dropped**, and
loses the sector it inherited from something it is not. `kind` grew from a
const to `["stock", "fund", "debt"]`, all three validating against
`stock.schema.json`. `v1/stocks/AT0000A2H326.json` reads `"kind": "debt"` with
no sector, against *Consumer Discretionary* before.

**Both rules come from one OpenFIGI sweep**, and they partition it: **322
records keyed by another company's ISIN**, and **571 non-equities of which 554
publish a sector they do not have**. The **615** this document carried until
2026-09-03 was an over-count by exactly 44 -- it swept the index's 9,400 ISINs,
which include the 44 belonging to ETF records already correctly typed in
`v1/etfs/`. Earlier figures in `TASKS.md` -- 104, 164, 622 -- were floors from
narrower detectors and should not be quoted either.

Gate, on the rebuilt tree: **221 passed** (111 and 4 skipped on the bare
install), and `python scripts/validate.py v1/` **exits 0**.

## What the rebuild's rehearsal turned up, and what it cost

Rehearsing into a `--out` tree first is what `AGENTS.md` asks for and it earned
its 44 minutes three times over. None of the following was visible from reading
the code:

1. **The 615 over-count above.** Caught because the build's own log line
   reports 571 and the arithmetic on the index reconciles: 9,078 = 9,356 - 322
   + 44.
2. **T19 reaches ETF output.** `normalize._enrich_holding` joins holdings on
   ISIN, ticker, then CUSIP, so disowning an ISIN removes a leg of that join.
   `EFA`, `IEFA`, `SCHF` and `VEA` gain 2.4 to 3.1 points of `Unknown` sector.
   That is the axis becoming honest -- the weight was previously booked into
   the mis-keyed record's sector -- but `VEA` now sits 5.5 points from T13's
   0.5 omit threshold for a reason unrelated to `VEA`.
3. **One record is silently dropped every build**, on a shard-key collision
   between two ISIN-less FinanceDatabase rows for Eagle Point Credit. Raised as
   **T21**. It predates both rules and the rebuild neither caused nor fixed it.

Cost paid, and signed off: **322 published URLs stopped resolving and 322
started.** A record that loses a wrong ISIN re-keys to its symbol. Every new
key was checked for a collision against the published tree before the rebuild
ran -- none.

Timing, worth keeping because it is the first rebuild with an OpenFIGI sweep in
it: **5m13s to build** and 72s to validate warm, against 44 minutes when the
sweep was cold. `.http_cache` held no OpenFIGI responses before 2026-09-03, so
the 940-request unauthenticated sweep is the whole difference. CI is always
cold and has the key, which is the case the 90-minute timeout is sized for.

## What is open, with nothing in flight

Not a plan -- a list, because choosing the next change is not this document's
to make:

- **T21**, the shard-key collision. Small, and it must not be bundled into a
  rebuild, since fixing it changes the record count.
- **T18** is still open and none of the above closes it. A depositary receipt
  is deliberately an equity here: the record describes the right company under
  the wrong security's identifier. OpenFIGI cannot fix it -- its mapping
  response carries no ISIN field -- and GLEIF reaches only 777 of the 2,142,
  missing Hon Hai and TSMC entirely.
- **The listing-metadata cluster** from the client-integration review: `XNAS`
  never emitted, `.DU` resolving to Dubai, 19,401 listings on an unmapped
  suffix, and `currency` inferred from a guessed MIC rather than read from the
  source columns that carry it. They are one cheap fix and they gate **W4**.
- **T15 is on hold by decision** and waits for a source that carries TSMC's
  Taiwan line rather than aliasing it to the NYSE ADR. Expect the same answer
  for any future per-holding alias. **No phase owns finding that source**,
  which is what actually blocks it.

**Still open: T15's provenance question**, and it is smaller than it reads.
`v1/etfs/SCHD.json` already publishes a FinanceDatabase-derived sector axis
under an EDGAR-only provenance block, so the bridge would add a fourth
identifier leg to an existing three-leg join rather than a new source of data.
Per-axis provenance would be cheap -- three blocks across 49 ETF records -- and
buys a consumer nothing, since provenance exists here for takedown and audit
and no client-side task reads it. Holding T15 means nothing waits on it.

## Two things to know before touching the pipeline

- **`normalize.py` imports no source module, and must stay that way.** It is
  importable with `requests` and `pandas` absent, which is what keeps the bare
  install runnable. `apply_instrument_identity` takes plain dicts for that
  reason, and `build.figi_identity` computes them.
- **Never use composite FIGI as evidence about an ISIN, in either direction.**
  As a detector it fires on 1,242 records; as an *exonerating* signal it agrees
  for 97 of the 152 flagged records carrying one, including `ARCHER DANIELS
  MIDLAND` against `ADMIRAL GROUP PLC`. A record's `composite_figi` comes from
  the same source row as its wrong ISIN, so it is contaminated by the defect it
  would be vouching against.

## Two upstream facts that have not changed

- Upstream is on standby and the seven open pull requests have still never been
  through CI. P1 needs write access nobody here has.
- Work still lands on `origin/main` and each change still keeps an
  upstream-mergeable branch. That this fork publishes does not change where
  changes are offered.
