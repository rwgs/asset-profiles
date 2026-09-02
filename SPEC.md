# Project specification

What the project must do and the boundaries it stays inside. This document holds
requirements rather than implementation: a change to how something is built does
not belong here, and a change to what counts as correct does.

The original design spec, `docs/asset-profiles-spec.md`, is dated 2026-05-09 and
still marked *Proposed*. It remains useful for shapes the code has not reached.
Where the two disagree, this document is current.

## Problem

A portfolio tracker cannot describe what a holding is exposed to without
reference data: which sector a company trades in, which country it is domiciled
in, and for a fund, how its holdings split across sectors, countries, and asset
classes.

Without this project, a client has three options and all three fail. Yahoo
Finance carries the data but its terms forbid redistribution, so every user must
fetch it themselves, and it publishes no geographic breakdown for funds at all --
measured live on a UCITS ETF, an eleven-sector breakdown arrives and a country
breakdown never does. Alpha Vantage returns fund constituents without a country
per line, so a country rollup needs a second lookup per constituent, about 1,500
of them for a world tracker, against a 25-request-per-day free tier. A
hand-maintained mapping inside each client duplicates the same work per client
and goes stale silently.

The measured consequence in the consuming client: of 69 ETFs in a real
portfolio, zero carried a geographic breakdown, against 50 that carried sectors.
Region coverage sat at 5.2% of assets while instrument type and asset class sat
at 96%. The classifier was not failing; nothing ever gave it a country.

## Users

Two audiences, with different constraints.

**Wealthfolio clients**, the primary consumer. They run on a user's own machine
or a self-hosted server, hold no shared secret, and cannot be assumed to have
any API key. They may be offline, and they may be running a build months older
than the current dataset. They cannot be asked to migrate in step with a schema
change. They need a lookup keyed on what they actually hold -- a ticker, often
with a Yahoo-style exchange suffix, sometimes an ISIN.

**Third parties and contributors** reading the dataset directly over the CDN or
opening a pull request. They have no access to this repository's secrets, cannot
run the weekly job, and can only fix a record through `manual_overrides/`. They
are bound by CC-BY-NC-SA 4.0 on the data and MIT on the code.

## Required behavior

- `v1/index.json` resolves a ticker or an ISIN to the path of a record, and
  states `schema_version`, `generated_at`, `next_refresh_at`, and per-kind
  counts.
- Every path the index names resolves to a file that exists and validates.
- A stock record carries name and listings, and where upstream knows them,
  sector, industry, country with an ISO 3166-1 alpha-2 code, and identifiers.
- An ETF record carries name and listings, and where the filing or issuer
  publishes them, `sector_weights`, `country_weights`, `asset_class_weights`,
  `top_holdings`, `holdings_count`, and `as_of_date`.
- Weights are decimal fractions. Each weighted list sums to 1.0 +/- 0.005, and
  `top_holdings` sums to no more than 1.0.
- A weighted list is present only when it carries signal. A list that is
  overwhelmingly one synthetic bucket -- `Unknown`, `Other` -- is not an answer
  and must be omitted rather than shipped at a plausible-looking 1.0.
- `country_code` values are real ISO 3166-1 alpha-2 codes. A filing's
  placeholder, such as N-PORT's `XX`, is not one and does not reach a record.
- Missing means omitted. No field is ever `null`, and a client reads absence as
  unknown rather than as zero.
- Every record carries `provenance`: `source`, `source_url`, `fetched_at`, and
  `license`.
- A record whose generated form fails validation is not written, does not enter
  the index, and is reported. One bad record never aborts the build; one bad
  source never empties the dataset.
- A file in `manual_overrides/` is deep-merged over the generated record before
  validation, and the merged result is what must validate.
- A record that leaves the universe or the upstream source has its shard removed
  and its index entries dropped.
- `next_refresh_at` is a commitment. If the refresh has not run by then, the
  published dataset is misreporting its own freshness and that is a defect, not
  a delay.

### Error, empty, and recovery cases

- A shard key must be usable as a single filename on Linux, macOS, and Windows.
  A key containing a path separator, or matching a Windows reserved device name,
  must be escaped before it reaches the filesystem or rejected -- never written
  as a path the index cannot address and the validator cannot see.
- Two records must never contend for one shard path. A collision is an error to
  report, not a silent overwrite.
- The build must be reproducible on Windows: text is read and written as UTF-8
  explicitly, and diagnostics are printable in the host console encoding.
- EDGAR returning no filing for a fund falls back to the issuer scraper. Both
  failing records an error against that ticker and leaves the previous shard
  untouched.
- A source whose schema changed upstream must fail loudly at the point of
  parsing rather than emit records with silently empty fields.

## Consumer interface

There is no user interface. The interface is HTTP GET over a CDN, and the
contract is the schema plus the URL shape.

- Base URL is configurable in the client. The default is jsDelivr against
  `wealthfolio/asset-profiles@main`, and a tag serves as an immutable pin.
- The primary workflow is: fetch `index.json` once, cache it, then lazily fetch
  the shard for each held symbol.
- The client resolution ladder is exact symbol, then ISIN, then the symbol's
  base with each candidate MIC, then the bare base symbol, then miss.
- A miss is a normal outcome, not an error, and the client falls back to its own
  enrichment.
- Accessibility is the consuming client's concern. This project's equivalent
  obligation is that a record is self-describing: display labels travel next to
  their codes, so `country` accompanies `country_code` and no consumer needs a
  private lookup table to render a breakdown.

## Architecture and data flow

GitHub Actions runs `scripts/build.py` weekly. It pulls stock rows from
FinanceDatabase, then for each fund in `config/etf_universe.yml` tries SEC EDGAR
N-PORT and falls back to an issuer holdings file. Records are normalized,
overridden, validated, and written as one JSON file per record under `v1/`, with
`v1/index.json` rebuilt from what is on disk. The job commits and pushes when
something changed. jsDelivr serves the repository directly; there is no server
and no database.

State ownership:

- Upstream sources own the facts. This project owns only normalization,
  aggregation, and attribution.
- `config/etf_universe.yml` owns which funds exist in the dataset.
- `manual_overrides/` owns corrections, and outranks the generated record.
- `v1/` is derived state, owned by the build, and safe to delete and regenerate.
- `.http_cache/` is a local fetch cache, untracked, and safe to delete.

External interfaces crossed: FinanceDatabase over raw GitHub, SEC EDGAR
submissions and Archives, issuer holdings endpoints via `etf-scraper`, GitHub
for commits, and jsDelivr for delivery.

## Security and privacy

- No user data of any kind enters this repository. There is nothing per-user to
  leak, and coverage is never derived from what real portfolios hold.
- The build holds no secret. `SEC_USER_AGENT` is a contact string, published on
  purpose, and the push uses the workflow's own `contents: write` token.
- Trusted: SEC EDGAR, FinanceDatabase, and the issuer files, in that order. All
  are trusted for content and none for shape -- a field that fails the schema is
  dropped, whichever source supplied it.
- Not trusted: the filesystem-safety of any upstream identifier. Symbols arrive
  containing path separators today.
- Legal exposure is managed by attribution rather than by obscurity. Provenance
  per record, MIT on code, CC-BY-NC-SA 4.0 on data, a published takedown contact
  and a seven-day commitment.
- Robots and rate limits are honored by routing every fetch through
  `http_cache.py` at one request per second per host.

## Performance and compatibility

- Refresh completes inside the workflow's 45-minute timeout.
- No single published file exceeds 50 MB, jsDelivr's per-file limit.
  `index.json` is 12.4 MB today; past 50 MB it shards by symbol prefix.
- The repository stays inside GitHub's 100 MB per-file limit and well inside its
  5 GB repository guidance. `v1/` is about 400 MB across roughly 98,000 files
  and `.git` is about 126 MB.
- A client resolves a symbol without downloading the dataset: one index fetch,
  then one small fetch per holding.
- Python 3.12 or newer. The build runs on `ubuntu-latest` in CI and must also
  run on Windows and macOS for development.
- Schema compatibility: additive optional fields bump the minor version and stay
  at the same path. A rename or a type change bumps the major version and moves
  to `/v2/`, with `/v1/` live for at least six months.

## Non-goals

- Real-time or historical quotes, OHLCV, or anything from an exchange feed.
- Fundamentals, earnings, dividend history, ratings, analyst targets, or news.
- Any per-user or portfolio-derived data, including deriving the ETF universe
  from what users hold.
- Comprehensive global coverage. The target is the funds real portfolios
  actually hold, not every fund in existence.
- Data derived from Yahoo Finance, at any remove.
- Proprietary taxonomy labels, and the names of those taxonomies.
- Serving this dataset from project-owned infrastructure. A CDN over a git
  repository is the whole delivery mechanism.
- The client-side integration itself, which lives in the Wealthfolio repository.
  This project owes it a dataset and a stable contract, nothing more.

## Acceptance criteria

- `python scripts/validate.py v1/` exits 0 on Linux, macOS, and Windows, on a
  fresh clone, with no environment variable set to make it work.
- Every shard on disk is reachable from `index.json`, and `counts` equals both
  the number of shards on disk and the number of distinct paths the index names.
  Verified by the validator, which must fail when a shard is unreachable.
- No shard path contains a directory separator beyond the `stocks/` or `etfs/`
  prefix, and no shard stem matches a Windows reserved device name. Verified by
  a test over generated keys, including keys observed upstream such as `BRK/A`
  and `CON`.
- Two funds that share a filer CIK produce different records. Verified against
  four funds in one trust, each matching its own published holdings.
- No published `sector_weights`, `country_weights`, or `asset_class_weights`
  list is majority-synthetic. Verified by a validator rule that fails such a
  record, and by a build report of per-fund unknown share.
- Every `country_code` published resolves in `pycountry`. Verified by a
  validator rule, with `XX` as the regression case.
- Each fund in `config/etf_universe.yml` either produces a record or is reported
  as a named failure with its reason. Neither silence nor a stale shard counts
  as a pass.
- `index.json` `next_refresh_at` is in the future whenever the dataset is
  served. Verified by a scheduled check that fails when the published dataset is
  past its own refresh date.
- A `manual_overrides/` file survives a rebuild and the merged record validates.
  Verified by a test with a fixture override.
- The commands in `README.md`, `CONTRIBUTING.md`, and `AGENTS.md` run as
  written on a clean machine. Verified manually per release, since nothing
  automated reads them.

## Unresolved questions

- What keeps the weekly refresh running once restarted. **Why it stopped is
  answered**: nine scheduled runs failed on a 404 between 2026-06-07 and
  2026-08-02 after FinanceDatabase moved its CSVs, then the schedule stopped
  firing entirely, consistent with GitHub's 60-day inactivity disable. What is
  still open is what notices next time, since nine identical failures went
  unremarked for two months. Answered by the freshness check this document
  already requires.
- Whether share classes need separate universe entries. The client's portfolio
  holds `VWRP`, the accumulating class; the universe lists `VWRL` and `VWCE`.
  Answered by measuring the consuming client's holdings against the universe.
- Whether an ETF whose holdings cannot be sourced should publish a
  metadata-only record, or no record. A metadata-only record resolves in the
  index and returns nothing useful; no record makes the client fall straight
  back to its own enrichment. Answered by what the client does with each.
- Whether the target is still about 300 funds, given that 13 non-US entries
  currently produce nothing and the consuming portfolio is mostly LSE-listed
  UCITS. Answered by the coverage measurement owed in `TASKS.md`.
- Whether tags are cut per refresh or per schema change. `README.md` documents
  pinned `@v1.0.0` URLs and no tag exists, so those URLs 404 today. Answered by
  the versioning decision in `DECISIONS.md` once the tagging cadence is set.
- Whether fork pull requests should stay behind CI approval. Five are open and
  `validate-pr.yml` has never run against any of them, so the only automated
  check the project has is not applied to proposed changes -- which is where it
  is worth most. Answered by the repository owner.
