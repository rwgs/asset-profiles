# Changelog

Changes that consumers of this project need to know about, newest first.

**Audience:** anyone fetching this dataset over the CDN -- the Wealthfolio
clients and third-party readers -- plus maintainers running the pipeline on
another machine. Entries describe effects on those readers, not commits.
Pipeline internals, documentation, and test changes belong in the git history.

No release has been tagged. Entries are dated because there is no version to
name them by, and `README.md`'s pinned `@v1.0.0` URLs do not resolve.

## Unreleased

- **`kind` will gain two values on a stock record, and about 322 shard paths
  will move.** Both land the next time `v1/**` is rebuilt; the rules are in the
  pipeline now and the published tree does not reflect them yet.
  - A record under `stocks/` may read `kind: "fund"` or `kind: "debt"` as well
    as `"stock"`. A consumer that assumes `"stock"` there, or that switches on
    the value, needs a branch. **615 records are affected** -- 478 notes and
    structured certificates, 137 fund shares -- and each also **stops
    publishing `sector`, `industry_group` and `industry`**, which it had
    inherited from its underlying rather than having of its own. Read an absent
    field as unknown, which is already this dataset's contract. `kind: "etf"`
    under `etfs/` is unchanged.
  - **322 records will drop an ISIN that belongs to a different company** and
    re-key to their symbol, so `stocks/CA18452Y1007.json` becomes
    `stocks/AIR.json` -- it reads AAR Corp. today under Clean Air Metals'
    identifier. Those ISIN paths and their `index.json` entries disappear. If
    you resolve through `index.json`, as the resolution ladder intends, nothing
    breaks; if you construct shard URLs from an ISIN you hold, those 322 will
    404. The freed ISIN is **not** reassigned to the company that owns it,
    because the source publishes no ISIN for it either.

- **The published dataset is stale and misreports its own freshness.** The last
  refresh committed on 2026-05-31 and `v1/index.json` advertises
  `next_refresh_at: 2026-06-07`. A consumer that trusts `next_refresh_at` to
  decide when to re-fetch will re-fetch constantly and get the same May data.
  Treat the current dataset as a **2026-05-31 snapshot** until a refresh commit
  appears. Cause: FinanceDatabase moved its CSV exports, so nine consecutive
  scheduled builds failed on a 404 between 2026-06-07 and 2026-08-02, after
  which the schedule stopped firing at all. The upstream URL fix is open as
  PR #1. Tracked as Phase 4 in `ROADMAP.md`.
- **ETF records are not reliable and should not be consumed yet.** Ten funds
  have records. Six of them -- `SCHD`, `SCHB`, `SCHX`, `SCHF`, `RSP`, `VNQ` --
  publish a majority fixed-income asset mix for what are equity funds, because
  funds that share a filer are not told apart: the four Schwab records carry
  byte-identical holdings, as do `ARKK` and `ARKG`. Six of the ten publish a
  `sector_weights` list that is entirely the synthetic `Unknown` bucket at a
  valid-looking sum of 1.0, and two more are 79% and 30% `Unknown`. Stock
  records are unaffected. Tracked as Phase 2 in `ROADMAP.md`.
- **No fund outside the US has a record.** All 13 non-US entries in the tracked
  universe -- 8 UCITS and 5 TSX-listed -- currently produce nothing. If you are
  reading this dataset for the geographic exposure of a UCITS fund, it has none
  to give you today. Tracked as Phase 3 in `ROADMAP.md`.
- **Fixes are open but unmerged.** PR #6 makes each fund resolve its own N-PORT
  filing, which is the fix for the ETF entry above, and reports that 19 of the
  52 configured US filer CIKs are wrong. Nothing in this section has landed, so
  none of it has changed what the CDN serves.
- **The repository cannot be cloned on Windows.** `git clone` fails with
  `invalid path 'v1/stocks/CON.DE.json'` -- Windows resolves that name to the
  console device -- and because it fails while building the index it leaves the
  working tree **empty**, not merely missing those two records. This affects
  anyone cloning the repository; it does not affect consumers fetching over the
  CDN. A fix is open as PR #5. Separately, 13 records are written into
  subdirectories the index does not name, so no consumer can reach them;
  fetching one returns 404 rather than wrong data. Tracked as Phase 1 in
  `ROADMAP.md`.

## 2026-05-31

- Weekly data refresh. No schema change. The last refresh to have run.

## 2026-05-10 through 2026-05-24

- Three weekly data refreshes on 2026-05-10, 2026-05-17, and 2026-05-24. Record
  contents changed as upstream sources changed; no schema change and no change
  to any URL.

## 2026-05-09

- First published dataset at `schema_version` **1.0.0**, under `/v1/`.
- `v1/index.json` resolves a ticker or an ISIN to a record path, and states
  `generated_at`, `next_refresh_at`, and per-kind counts.
- Roughly 98,000 stock records carrying name, listings, and where upstream knows
  them, sector, industry, country with an ISO 3166-1 alpha-2 code, market-cap
  band, and identifiers.
- ETF records carrying `sector_weights`, `country_weights`,
  `asset_class_weights`, `top_holdings`, `holdings_count`, and `as_of_date`.
- Every record carries a `provenance` block naming its source, source URL, fetch
  time, and license.
- Reading rules a consumer must implement: weights are decimal fractions and not
  percentages; a weighted list sums to 1.0 +/- 0.005; a missing field is omitted
  rather than `null` and means unknown, never zero.
- Licensing: data under CC-BY-NC-SA 4.0, code under MIT. Attribution is
  required. Takedown requests to `opensource@wealthfolio.app`, actioned within
  seven days.
