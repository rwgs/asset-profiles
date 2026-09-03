# Project decisions

Closed decisions that constrain future changes, newest first. Entries are
appended and never rewritten; a reversal is recorded by adding a new entry and
marking the old one superseded.

Record a decision only when it constrains future work and its rationale cannot
be recovered by reading the code. Routine implementation choices belong in the
diff.

The 2026-05-09 entries below were settled at bootstrap and are reconstructed
from `README.md`, `CONTRIBUTING.md`, and `docs/asset-profiles-spec.md` sections
13 and 15. They were load-bearing before they were written down here.

## 2026-09-03 This fork publishes; upstream stays the place changes are offered

Status: Accepted.

### Decision

`README.md` points jsDelivr at `rwgs/asset-profiles@main`, and the weekly
refresh runs here. `wealthfolio/asset-profiles` remains the upstream a change
is offered to, and each change keeps its upstream-mergeable branch, but it is
no longer what a client fetches.

### Why

Upstream is on standby, stated by its maintainer on 2026-09-03: *"this repo is
not used at all, it was an idea to curate stock and symbol profiles. but it's
en stand by"*. Its last commit is 2026-05-31, its scheduled refresh has been
failing since 2026-06-07 and stopped entirely after 2026-08-02, and seven pull
requests wait on a CI approval that has never been given. A dataset whose
publisher is not publishing does not serve a client.

Pointing here is a strict improvement even before a refresh runs, which is what
makes this safe to do now rather than after: the two trees hold the same
records from 2026-05-31, but this one has no shard nested under a directory, no
filename a Windows checkout refuses, and `counts` agreeing with both the files
on disk and the paths the index names. Upstream still has all three defects,
and its tree cannot be cloned on Windows at all.

### Rejected alternatives

- **Wait for upstream.** The maintainer has said they are not working on it.
  Waiting is a decision to serve stale, broken data indefinitely, taken by
  default.
- **Publish only after Phase 2 closes.** Six of the ten ETF records carry
  meaningless sector weights, which argues for finishing first. But those six
  are equally meaningless upstream, and the client is not integrated yet, so
  delaying changes nothing for a consumer while leaving the defects above
  served.
- **A branded domain or an API.** Both were rejected at bootstrap for reasons
  that have not changed; see the 2026-05-09 jsDelivr entry.

### Consequences

The weekly refresh becomes this repository's obligation, and `next_refresh_at`
is a commitment made from here. `SEC_USER_AGENT` must be set as a repository
secret before the first scheduled run or the ETF pass takes 403 from EDGAR;
it is deliberately not committed, being a contact address in a public
repository. The first refresh is also the first full rebuild since bootstrap,
so it will rewrite `v1/**` wholesale -- measured against the live source, from
98,463 stock records to 90,514, because upstream now publishes 30,378 rows
carrying an ISIN against 14,716 before and the cross-listing merge absorbs
them. Roughly 8,000 shard URLs stop resolving, which is why the rebuild is
sign-off work rather than a consequence of this entry.

Nothing here withdraws a pull request or changes where work is offered.

## 2026-09-02 `_` is the escape character for a filesystem-unsafe shard key

Status: Accepted.

### Decision

Where a shard key cannot be used as a filename, the offending part is escaped by
appending `_` to it rather than by substitution, deletion, or encoding. PR #5
applies this to a component whose head is a DOS device name (`CON.DE` becomes
`CON_.DE`) and `TASKS.md` T6 applies the same character to the path separator
(`BRK/A` becomes `BRK_A`). One convention, applied to both, composing where a
key needs both (`CON/A` becomes `CON__A`).

### Why

`_` is the only free character available. Measured 2026-09-02 by scanning every
stem in `v1/stocks/` and `v1/etfs/`: zero of the 98,462 flat stems contain `_`
and zero end in `_`, so no well-formed key changes and no escaped form can
collide with an unescaped one. Escaping only what the filesystem refuses is what
keeps all 98,462 working paths byte-identical, which matters because every one
of them is a URL a client may have cached.

### Rejected alternatives

- **Map `/` to `-`.** The obvious scheme, and the measurement rules it out:
  eleven of the thirteen nested keys already have a correct dash-form shard on
  disk (`BRK-A`, `AKO-A`, `AKO-B`, `BF-A`, `BF-B`, `BRK-B`, `CRD-A`, `CRD-B`,
  `HEI-A`, `HVT-A`, `WSO-B`), so it manufactures the exact collision the change
  exists to prevent. Only `BIO/B` and `RAC/WS` have no dash form.
- **Percent-encode.** Reversible and unambiguous on disk, unreliable as a CDN
  path segment: `%2F` is normalized back to `/` by enough intermediaries to fail
  in precisely the case it is meant to fix. `%` is otherwise free.
- **Drop any record whose key needs escaping.** Smallest possible change, and it
  silently loses `BIO/B` and `RAC/WS`, which have no alternate form.
- **Keep `shard_key` purely logical and escape at the write site.** Considered
  and reversed: `apply_overrides` resolves an override file by shard key, so a
  key that does not match the file on disk is a trap for a contributor. This is
  why #5 updates `manual_overrides/README.md` in the same change.

### Consequences

`shard_key` is filesystem-aware by contract, not by accident, and its docstring
says so. The escaped forms are new paths, so a client holding a cached
`index.json` keeps asking for the old one until its TTL expires; that URL 404s
rather than misresolving, which the spec already requires a client to tolerate.
`BRK_A` and `BRK-A` will both publish as separate records for one security --
the escape makes the duplicate visible and addressable, and does not resolve it.
Resolving it settles a data question and is raised separately.

## 2026-09-02 `SPEC.md` supersedes the original design spec

Status: Accepted.

### Decision

`SPEC.md` is the current statement of requirements.
`docs/asset-profiles-spec.md` is retained as reference for intended shapes the
code has not reached; where the two disagree, `SPEC.md` wins.

### Why

The design spec is dated 2026-05-09, still marked *Proposed*, and describes a
system in the future tense that has since been half-built. Its section 14 lists
phases that are done, its section 15 lists open questions that `README.md`
answers, and its section 12 describes a client integration that does not exist.
An agent reading it cold cannot tell which of those is a plan and which is a
description. Two documents both claiming to be the specification is worse than
either alone.

### Rejected alternatives

- Editing the design spec in place: it is a coherent record of what was intended
  on one date, and rewriting it destroys the ability to see how the project
  drifted from its own plan.
- Deleting it: sections 5, 7, 11, and 12 are still the only written account of
  the schema rules, the resolution ladder, and the client contract.

### Consequences

A requirement change lands in `SPEC.md`, never in `docs/`. The design spec is
now a historical document and will diverge further, which is expected rather
than a defect.

## 2026-05-09 Never publish data derived from Yahoo Finance, or anything priced

Status: Accepted.

### Decision

No record may contain data sourced from Yahoo Finance at any remove. Quotes,
OHLCV, fundamentals, dividend history, ratings, and analyst targets are out of
scope regardless of source.

### Why

Yahoo's terms forbid redistribution, and this dataset is redistribution by
construction -- a public git repository behind a public CDN. Priced and
fundamental data is separately the most heavily licensed category in the
industry, and a takedown against it would take the whole dataset down with it.
Profile data from MIT-licensed and public-domain sources is defensible in a way
that a mixed dataset is not.

### Rejected alternatives

- Yahoo for the fields no other source covers: it is precisely the field set the
  clients most want, which is what makes it tempting and what makes including it
  fatal.
- Fetching Yahoo at build time without storing it: the stored derivative is
  still a derivative.

### Consequences

The clients keep their own Yahoo path for what this dataset cannot supply, so a
gap here is a fallback there rather than a missing feature. Anything priced is
permanently out of scope, which also keeps the refresh cadence weekly instead of
daily.

## 2026-05-09 Use generic sector labels and never name a proprietary taxonomy

Status: Accepted.

### Decision

Upstream sector strings are mapped to descriptive labels in
`config/sector_taxonomy.yml`. Neither the labels nor any documentation names a
commercial classification standard.

### Why

Classification standards are licensed intellectual property, and the assertion
that a dataset *is* one of them is the part that draws attention -- more than
the strings themselves. Descriptive labels chosen independently carry no such
claim.

### Rejected alternatives

- Passing upstream sector strings through unchanged: it makes the dataset's
  vocabulary an accident of whichever source answered, and different sources
  disagree.
- Naming the standard for clarity: buys precision no consumer needs and takes on
  the one risk that has no upside.

### Consequences

Consumers get a vocabulary that is stable but not mappable to a commercial
standard without their own crosswalk. Adding a source means adding a mapping
block, not adopting its labels.

## 2026-05-09 EDGAR first for funds, issuer files only as fallback

Status: Accepted.

### Decision

Fund holdings come from SEC EDGAR N-PORT where a filing exists. Issuer-published
holdings are used only where EDGAR has nothing, and are attributed with an
`as_of_date`.

### Why

EDGAR is US public domain and involves no contract with anyone -- no terms to
breach and no page to move. Issuer files are published under the issuer's own
terms and reached by scraping, which is the grey part of the pipeline. Ordering
by legal exposure keeps the grey part as small as the coverage requirement
allows.

### Rejected alternatives

- Issuer files first, as they are better structured and pre-aggregate the
  geographic weights that are the whole point: it maximises exposure on the
  funds where EDGAR would have served.
- EDGAR only: it excludes every non-US fund, and UCITS funds are the ones the
  consuming client actually holds.

### Consequences

Non-US coverage depends on a third-party scraper library and on issuer pages
staying put, so it is structurally less reliable than US coverage and must be
allowed to fail per fund without failing the build. `etf-scraper` exposes no
session hook, so those fetches also bypass this project's own rate limiter.

## 2026-05-09 CC-BY-NC-SA 4.0 on the data, MIT on the code, provenance per record

Status: Accepted.

### Decision

`v1/**` is licensed CC-BY-NC-SA 4.0; `scripts/`, `schema/`, and the workflows
are MIT. Every record carries a `provenance` block naming source, URL, fetch
time, and license. A published takedown contact commits to acting within seven
days.

### Why

The dataset aggregates sources under different terms, so it cannot be more
permissive than its inputs. Share-alike and non-commercial keep it from being
absorbed into a commercial product, which is the outcome most likely to provoke
the upstreams. Per-record provenance is what makes a takedown surgical: without
it, a complaint about one source is a complaint about the whole dataset.

### Rejected alternatives

- A single license for the repository: the code is worth reusing freely and the
  data is not ours to give away that broadly.
- Aggregate attribution in `README.md` only: it cannot answer "where did this
  specific number come from", which is the question a dispute asks.

### Consequences

Provenance is a hard requirement, not a nicety -- a record that cannot be
attributed does not ship. Commercial consumers must ask. The non-commercial
clause also rules out some contribution paths that would otherwise be welcome.

## 2026-05-09 ISIN is the canonical record key, primary symbol is the fallback

Status: Accepted.

### Decision

A record's key is its ISIN when one is known, otherwise its primary symbol.
Cross-listings of one share class share a record and appear as multiple
`listings` entries; different share classes are different records. Resolution
happens through `index.json`, never by guessing a filename.

### Why

Symbols are neither unique nor stable: `SHOP` and `SHOP.TO` are one security,
`BLT` on two exchanges may be two, and `BRK.A` and `BRK.B` are genuinely
different. ISIN is the only identifier in the available sources that is both
globally unique and per-share-class. The index exists because the key cannot be
derived from what a client holds.

### Rejected alternatives

- Symbol as the key: collides across exchanges and changes under corporate
  actions.
- FIGI: better suited to venue-level identity, and upstream coverage is thin.
  `composite_figi` is carried so consumers can group later without this project
  having to.

### Consequences

Only about 15% of stock records carry an ISIN, so most are keyed by symbol and
inherit the instability the decision was meant to avoid -- and cross-listings
that share no ISIN cannot be merged. The key also becomes a filename, which is
where `TASKS.md` T2 and T6 come from -- and PR #5 has since made `shard_key`
explicitly filesystem-aware rather than purely logical.

## 2026-05-09 Publish static JSON from the git repository over jsDelivr

Status: Accepted.

### Decision

One JSON file per record plus a single `index.json`, served by jsDelivr directly
from the repository. No server, no database, no custom domain. Clients hold the
base URL as configuration so it can be redirected later without a code change.
If `index.json` approaches 50 MB it shards by symbol prefix.

### Why

The operational requirement was one weekly cron with no servers and no secrets
to rotate, because a dataset nobody has to operate is a dataset that survives
inattention. A per-record shard also means a client fetches kilobytes for a
holding rather than the whole dataset. jsDelivr's per-file limit of 50 MB is the
only ceiling that binds.

### Rejected alternatives

- `profiles.wealthfolio.app` from day one: a branded URL is a redirect away and
  cost nothing to defer. Revisit when usage warrants it.
- Bulk files by asset class: fewer requests, but every client downloads
  everything to answer one question.
- A queryable API: reintroduces a server, secrets, and per-user rate limits --
  the three things this design exists to avoid.

### Consequences

jsDelivr caches `@main` for around 12 hours, so a refresh is not instantly
visible and production clients should pin a tag. A repository holding roughly
98,000 files and 400 MB makes ordinary git operations slow, and a full rebuild
produces a diff no human can review. The 12.4 MB `index.json` is well inside the
limit today, so the sharding rule is a contingency rather than work.

## 2026-05-09 Curate the fund universe by hand and hold no user data

Status: Accepted.

### Decision

`config/etf_universe.yml` is edited by pull request. Coverage is never derived
from what real portfolios hold, and this repository contains no telemetry and no
per-user data of any kind.

### Why

Deriving the universe from user holdings is the obvious way to prioritise
coverage and would mean this repository's contents encoded what users own. A
public git history is a permanent one, so a privacy mistake here cannot be taken
back. Hand curation costs a pull request and carries no such risk.

### Rejected alternatives

- Opt-in reporting of missing-ticker resolutions: defensible with consent, and
  still moves user-derived signal into a public repository. If it ever happens,
  it happens in the client and stays there.
- Tracking every listed fund: unbounded work and a larger surface for issuer
  complaints, for coverage nobody asked for.

### Consequences

Coverage is decided by whoever opens the pull request rather than by demand,
which is why the coverage measurement in `TASKS.md` W6 must come from the client
side as an aggregate number and never as a holdings list.

## 2026-05-09 Corrections live in `manual_overrides/`, never in `v1/`

Status: Accepted.

### Decision

A wrong record is fixed by a partial JSON patch in
`manual_overrides/{shard_key}.json`, deep-merged over the generated record
before validation. `v1/**` is generated output and is never hand-edited.

### Why

A hand-edit to `v1/` is erased by the next refresh, silently and within a week,
so the contributor's work disappears and the same bug is reported again. Merging
before validation means an override cannot introduce a record that fails the
schema. Keeping the fix outside the generated tree also keeps it reviewable: the
patch is three lines where the regenerated record is a whole file.

### Rejected alternatives

- Accepting pull requests that edit a shard directly: the friendliest flow and
  the one that guarantees the fix does not survive.
- Correcting upstream only: right where possible and too slow to rely on, since
  FinanceDatabase and issuer files move on their own schedules.

### Consequences

Every fix is expressed against a shard key, so changing how keys are computed
changes where overrides must live. Lists are replaced wholesale rather than
merged element-wise, so correcting one holding means copying the generated list.
An override that upstream later makes redundant stays until someone prunes it,
and nothing currently detects that.

## 2026-05-09 Version by path prefix, with versions live side by side

Status: Accepted.

### Decision

Every record carries a semver `schema_version`. Additive optional fields bump
the minor version at the same path. A rename or type change bumps the major
version and moves to a new prefix, and the old prefix stays live for at least
six months.

### Why

Clients are installed software on other people's machines, updating on their own
schedule or not at all. A breaking change to a URL they already fetch breaks
builds this project cannot deploy to. Serving both versions makes the migration
the client's decision, and the six-month floor makes it a decision they have
time to make.

### Rejected alternatives

- Version negotiation by header: a static CDN over a git repository has no
  request logic to negotiate with.
- Additive-only forever: workable until a field's type is wrong, at which point
  the choice is a rename or living with it.

### Consequences

A breaking change means running two datasets and two build outputs for at least
six months, which roughly doubles repository size for the duration. That cost is
the reason to get the shapes right in `/v1/` rather than to iterate through
prefixes.
