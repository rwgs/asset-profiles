# The rebuild, waiting on sign-off

Nothing is mid-edit. What is in flight is a decision: the first full rebuild of
`v1/` since bootstrap, which four changes on 2026-09-03 have made both possible
and necessary, and which needs sign-off because it rewrites 98,000 files and
retires roughly 8,000 URLs.

## Why a rebuild is now the blocking step

Four pipeline changes landed, closing three of Phase 2's four items, and **none
of them can be seen in the published data**. `v1/` still holds records fetched
on 2026-05-31.

- `790b45e584` rejects a country code ISO 3166-1 never assigned. Four published
  records carry `XX`, so `validate.py v1/` now **exits 1 with 4 errors**. This
  is the only thing making the gate red, and only a rebuild clears it.
- `b8806b695d` resolves a holding's sector through CUSIP. SCHD's `Unknown`
  sector weight falls 13.0% to 1.5% -- in a rebuild.
- `209ddb2343` reports per-fund coverage. It showed a live ETF pass producing
  **38 records from 65 universe entries against the 10 published**.
- `d9bcbd11fd` absorbs the one record the index cannot reach.

Add `52fdc78ce3` from the day before, whose four Schwab records still hold the
byte-identical holdings a CIK-level lookup produced, and the gap between what
the pipeline does and what the dataset says is the whole of Phase 2's remaining
visible defect.

## What a rebuild would actually do

Measured against the live source on 2026-09-03, not estimated:

| | Published | After a rebuild |
| --- | --- | --- |
| Stock records | 98,463 | 90,514 |
| ETF records | 10 | 38 |
| Rows read | -- | 112,654, normalizing to 111,537 |
| Records with an unassigned country code | 4 | 0 |
| Records the index cannot reach | 0 (T5 retired them) | 0 |

**The stock count falls, and that is the part to weigh.** It is not data loss:
upstream now publishes 30,378 rows carrying an ISIN against the 14,716 records
that hold one here, so the cross-listing merge absorbs 21,022 rows into 9,356
canonical records instead of leaving them as separate shards. The dataset gets
more correct and roughly 8,000 shard URLs stop resolving. Every one of those is
a URL a client may hold, which is exactly the risk `ROADMAP.md` names for
Phase 1 and the reason this is sign-off work.

`generated_at` and `next_refresh_at` would finally move off 2026-05-31 and
2026-06-07, which is P2's acceptance signal and is still unspent.

## Two things that must be true first

- **`SEC_USER_AGENT` must be a repository secret on `rwgs/asset-profiles`.**
  `gh secret list` reports none, and EDGAR answers 403 without it, so the ETF
  pass would produce nothing and the refresh would publish a stocks-only tree.
- **The rebuild must not use `--no-stocks`.** The enrichment index comes from
  the in-memory stocks pass, so an ETF-only build silently gives every record
  100% `Unknown` sector weights. The 2026-09-03 probe shows exactly that.

## What is left in Phase 2 after it

One item: omitting a weighted list that is majority-synthetic rather than
renormalizing `Unknown` to 1.0, plus the validator rule that makes shipping one
an error. It is the only Phase 2 item that changes what the dataset publishes
rather than how it is built, and its cost moved: before CUSIP resolution it
would have removed `sector_weights` from six of ten records, and SCHD now
resolves to 1.5% `Unknown`. Re-measure against a rebuilt tree before choosing a
threshold. Read `SPEC.md` on absence meaning unknown, and W5 in `TASKS.md`.

## Two defects raised and not acted on

Both found by the coverage report on its first live run, both out of scope for
the change that found them, both in `TASKS.md` under the current phase.

- A negative weight fails the schema, and 11 of 49 EDGAR-sourced funds hit it.
  N-PORT reports short positions; `SH`, an inverse fund, carries `-0.239799`.
  Deciding whether the dataset represents a short position settles what it
  publishes.
- `build.py --no-stocks` silently drops the sector axis, as above.
