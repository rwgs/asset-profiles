# In flight: the pipeline half of T19 and T20 has landed; the rebuild has not

Two published data defects now have rules that correct them, and `v1/` has not
been rewritten to apply either. That split is deliberate -- a pipeline change
and the 98,000-file diff it causes are separate commits -- and it is the whole
of what is outstanding.

## What landed

**T19: a record keyed by another company's ISIN loses the ISIN** and re-keys to
its `primary_symbol`. AAR Corp. stops being published as Clean Air Metals'
identifier. Two independent signals are required, because either alone is too
loose: OpenFIGI names a different company, *and* the ISIN's country prefix is
an assigned ISO country that disagrees with the record's own `country_code`.

**T20: a record that is not an equity is retyped rather than dropped**, and
loses the sector it inherited from something it is not. `kind` grew from a
const to `["stock", "fund", "debt"]`, all three validating against
`stock.schema.json`.

**Both rules come from one OpenFIGI sweep of all 9,400 published ISINs**, and
they partition it: **322 records keyed by another company's ISIN**, and **615
non-equities of which 554 publish a sector they do not have**. Earlier figures
in `TASKS.md` -- 104, 164, 622 -- were floors from narrower detectors and
should not be quoted.

Gate: **221 passed** (111 and 4 skipped on the bare install), and
`python scripts/validate.py v1/` still **exits 0**. A `--limit 4000 --out`
probe build exercises both rules and validates clean.

## What is outstanding, in order

1. ~~Set `OPENFIGI_API_KEY` as a repository secret.~~ **Done 2026-09-03 at
   20:59Z**, confirmed with `gh secret list`. The sweep is now 94 requests and
   under a minute in CI rather than 940 and ~39 minutes. **Its value has never
   been exercised**, here or on a runner, because the secret is not readable
   and was not set locally -- so Sunday 06:00 UTC is the first test of it. A
   rejected key exits 2 rather than publishing a dataset with none of the
   corrections applied, which is what makes that first run safe to leave
   unattended. To check it sooner, set it locally and run:
   `python -c "import sys; sys.path[:0]=['scripts','scripts/sources']; import openfigi; print(openfigi.max_jobs_per_request(), len(openfigi.map_isins(['US0378331005'])))"`
   -- it should print `100 1`, and raise `CredentialError` if the key is wrong.
2. **Rebuild `v1/`, with sign-off.** Now the next action, and the one that
   matters: it applies both rules to the published tree, which is where the
   defects actually stop being served. It moves roughly 322 shard paths,
   because a record that loses its ISIN re-keys to its symbol, so it removes
   URLs as well as changing files. Rehearse into a `--out` tree
   first, as T14 and T16 both did, and keep it a commit holding nothing but
   `v1/**`.
3. **T18 is still open and is not closed by any of this.** A depositary receipt
   is deliberately an equity here: the record describes the right company under
   the wrong security's identifier. OpenFIGI cannot fix it -- its mapping
   response carries no ISIN field -- and GLEIF reaches only 777 of the 2,142,
   missing Hon Hai and TSMC entirely.

## Two decisions taken, and one still open

**Taken 2026-09-03, and both went against the recommendation put first.** T19
drops the wrong identifier; T20 keeps the record and corrects it. Read together
they are one rule: a published record is worth keeping and worth making honest,
while a field known to be wrong is not worth keeping at all.

**T15 is on hold by decision.** It waits for a source that carries TSMC's
Taiwan line rather than aliasing that ISIN to the NYSE ADR's record. The alias
was one line and cleared all four funds; it was rejected because it asserts an
equivalence between two distinct securities that OpenFIGI declines. Expect the
same answer for any future per-holding alias. **No phase owns finding that
source**, which is now what blocks the task and the thing to raise before it is
picked up again.

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
