# Nothing in flight. T23 is closed in code and in data

The arc that has been running since the OpenFIGI sweep is finished. T19, T20
and T23 are all on `main` *and* applied to `v1/`, so every defect they correct
has stopped being served rather than only stopped being produced.

**T23's rebuild is `66f8afc92e`**, committed on its own as `AGENTS.md`
requires: `diff: +11 / ~90551 / -11`, 90,570 files changed. A listing's venue
and currency now come from the source's own `mic` and `currency` columns
rather than from a guess at the Yahoo symbol suffix. Apple's record
(`US0378331005`) reads `AAPL` at `XNAS` against `XNYS` before, and `APC.DU` at
`XDUS` in `EUR` against Dubai's `DIFX` in `AED`.

**The scheduled refresh is no longer carrying an unreviewed publish.**
`refresh.yml` fires Sunday 06:00 UTC and auto-commits `v1/**` as the bot. Until
tonight it would have published T23's 47,285 listing corrections with nobody
reading the diff. It now has almost nothing left to change, which also makes it
a safe first exercise of `OPENFIGI_API_KEY` -- set 2026-09-03 at 20:59Z and
never yet used anywhere. A rejected key exits 2, and now that costs a failed
run rather than a wrong dataset.

## What the rebuild cost, and what it turned up

Rehearsing the whole build into a scratch tree first is what `AGENTS.md` asks
for, and the rehearsal reconciled to the real build exactly -- same 8,520 of
9,356 ISINs typed, same 323 dropped, same index. It also found three things the
task had not predicted, none visible from reading the code:

1. **11 published URLs retire and 11 start**, where T22's were 322. Every one
   is a group the source had already merged across two different companies
   under a shared ticker, so T23 only decides which of the two names wins:
   `SE0001174970.json` (Millicom) becomes `MIC.json` named *Macquarie
   Infrastructure*. Checked rather than assumed -- every retired key's listing
   symbols still resolve in the new index, so no record is dropped.
2. **29 of 49 ETF records change `sector_weights`**, every one toward *less*
   `Unknown`: largest -0.44pp, no axis gained or lost, nothing brought near
   T13's 0.5 omit threshold. The opposite of T19's effect on the same axis,
   and for the same reason -- a better primary means a better holdings join.
3. **1,919 records' `figi` changes and 265 lose it outright.** That is now
   **T24**, and it is the one finding worth acting on.

## T24 is the open question this raised

`group_cross_listings` promotes on a single test -- `exchange_mic` in
`{XNYS, XNAS, ARCX, BATS}` -- and `sorted` is stable, so a group with no US
member keeps source order. While `""` mapped to `XNYS` that test was true for
nearly every record and the rule barely discriminated. With real MICs it does,
and the fallback is now visible: of 1,997 changed primaries, **781 move to a
genuine US venue** (the intended fix) and **161 move to an LSE `0XXX.L`
international-board line** (not). STRABAG SE names `0MKP.L` rather than
Vienna's `STR.VI`.

It matters beyond display because `identifiers` comes from the primary
listing's source row, and composite FIGI is the best-covered identifier here --
42,817 against 9,400 ISINs -- and what T15's holdings bridge would join on.

**`OTCM` is the lever and the reason this is a product question.** 11,745
listings moved `XNYS` to `OTCM`, `is_us` does not count it, and **822 records
have no US MIC but do have an OTC line** that would win if it did. Whether a US
over-the-counter line should outrank a European company's home venue is the
call T24 exists to make. Do not widen `is_us` without making it -- that moves
822 records a second time.

## What else is open, with nothing in flight

Not a plan -- a list, because choosing the next change is not this document's
to make:

- **T24**, above. Needs the product call before any code, and like T21 must not
  be bundled into a data rebuild, since it changes shard keys.
- **T21**, the shard-key collision. One record is still silently dropped every
  build on the `ECC` pair, and every build still logs it.
- **T18** is still open and none of the above closes it. A depositary receipt
  is deliberately an equity here: the record describes the right company under
  the wrong security's identifier. OpenFIGI cannot fix it -- its mapping
  response carries no ISIN field -- and GLEIF reaches only 777 of the 2,142,
  missing Hon Hai and TSMC entirely.
- **T15 is on hold by decision** and waits for a source that carries TSMC's
  Taiwan line rather than aliasing it to the NYSE ADR. **No phase owns finding
  that source**, which is what actually blocks it.
- **W4 is no longer gated.** Four of the five listing-metadata defects that
  held it back are fixed in the data.

## Two things to know before touching the pipeline

- **`normalize.py` imports no source module, and must stay that way.** It is
  importable with `requests` and `pandas` absent, which is what keeps the bare
  install runnable. `apply_instrument_identity` takes plain dicts for that
  reason, and `build.figi_identity` computes them.
- **Never use composite FIGI as evidence about an ISIN, in either direction.**
  A record's `composite_figi` comes from the same source row as its wrong ISIN,
  so it is contaminated by the defect it would be vouching against.

## Two upstream facts that have not changed

- Upstream is on standby and the seven open pull requests have still never been
  through CI. P1 needs write access nobody here has, and is not worth waiting
  on -- the check it names is being run on *this* fork instead, which is what
  `validate-pr.yml` gaining a `workflow_dispatch` trigger is for.
- Work still lands on `origin/main` and each change still keeps an
  upstream-mergeable branch. That this fork publishes does not change where
  changes are offered.
