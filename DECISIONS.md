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

## 2026-09-03 OpenFIGI may correct an instrument's type, and a wrong ISIN is dropped

Status: Accepted. Widens *Adopt OpenFIGI as an identifier-mapping source*
below, which said no published field may take its value from OpenFIGI. That
clause is now narrower than it reads: it still holds for every field a client
classifies on -- sector, industry, country, weights -- and no longer holds for
`kind`.

### Decision

Three things, decided together because they are one question wearing three
hats: what does this dataset do when the source hands it something wrong?

1. **A record's `kind` may be set from OpenFIGI's `securityType2`.** `stock` is
   an equity, and `fund` and `debt` are the two kinds the stocks tree turns out
   to contain. A retyped record also **loses `sector`, `industry_group` and
   `industry`**, which it had inherited from something it is not. `stock.schema.json`
   carries all three kinds; `v1/etfs/` keeps its own schema, because only an
   ETF record carries holdings.
2. **An ISIN OpenFIGI attributes to a differently-named company is dropped**,
   and the record re-keys to its `primary_symbol` through `shard_key`. Two
   independent signals are required: the name disagrees, *and* the ISIN's
   country prefix is an assigned ISO country that disagrees with the record's
   own `country_code`.
3. **The records stay.** A certificate or a fund share is corrected rather than
   filtered out of the dataset, so no shard URL disappears.

### Why

Measured 2026-09-03 over the published tree, typing all 9,400 ISINs: **615
records are not equities** -- 478 notes and structured certificates, 137 fund
shares -- and **554 of them publish a sector they do not have**.
`v1/stocks/AT0000A2H326.json` is a leveraged certificate over Daimler, typed
`stock`, carrying *Consumer Discretionary* borrowed from its underlying. And
**322 records are keyed by an ISIN belonging to another company**: `Dave &
Buster's Entertainment` under an iShares ETF's ISIN, `Camden National
Corporation` under `AMUNDI CAC 40`, AAR Corp. under Clean Air Metals'.

Nothing already in the pipeline can tell any of this. FinanceDatabase carries
no instrument type, and it is the source of both defects -- so the only way to
know a record is not a share is to ask something that does. That is why the
narrower clause had to move: refusing OpenFIGI a value means publishing 554
wrong sectors to protect a rule whose purpose was to stop exactly that.

Correcting rather than filtering is the owner's call, taken 2026-09-03: a
published record is worth keeping and worth making honest, while a field known
to be wrong is not worth keeping at all. Deleting the record would remove a URL
a client may hold and discard the part that was right.

### Rejected alternatives

- **Filter non-equities out of `v1/stocks/` entirely.** Smallest change and it
  makes the count zero, but it removes 615 shard URLs and tells a client
  holding one of them nothing at all.
- **Keep a wrong ISIN and mark the record.** Publishes a join known to be
  wrong, and a consumer that ignores the new field is handed a different
  company in a different country and sector.
- **A name rule over the `EGB OE` and `RCB OE` prefixes.** Needs no third
  party and catches 443 of the 478 notes, but nothing generalises it to the
  fund shares, and it hard-codes two issuers' naming into the pipeline.
- **Composite FIGI as evidence about an ISIN**, in either direction. It fires
  on 1,242 records as a detector, and as an *exonerating* signal it agrees for
  97 of the 152 flagged records that carry one -- including `ARCHER DANIELS
  MIDLAND` against `ADMIRAL GROUP PLC`. The record's `composite_figi` comes
  from the same source row as its wrong ISIN, so it is contaminated by the
  defect it would be vouching against. Do not retry this.
- **One signal instead of two for a wrong ISIN.** The name check alone fires on
  888 records, most of them notes and certificates whose name differs from
  their issuer's legitimately, plus corporate renames -- `Orocobre Limited` is
  now `ALLKEM LTD`. The country check alone fires on 1,927, of which the
  offshore incorporations are correct.

### Consequences

The rule is a floor and it is not perfect, measured rather than claimed.
Precision on the 322 is high but under 100%: spot-checking found corporate
rebrands whose new name shares no token with the old and whose domicile is
offshore, so both signals fire -- `Foxconn Interconnect Tech.` is now `FIT HON
TENG LTD`, `WANdisco plc` is `CIRATA PLC`. Those lose a correct ISIN. Heavy
abbreviations do too: `Industrial & Commercial Bank of China` against `IND &
COMM BK OF-UNSPON ADR`. A `difflib` ratio guard at 0.83 removes the
transliteration class and deliberately does not chase the rest, because each
further guard costs true positives and tunes on single records.

Recall is a floor for a different reason: it only sees the 8,564 ISINs OpenFIGI
resolved of 9,400 published, and only the 9,400 of 90,513 records that carry an
ISIN at all.

The refresh workflow's timeout moved from 45 minutes to 90, and the build now
reads an optional `OPENFIGI_API_KEY`. Unauthenticated, typing every ISIN is 940
requests and about 39 minutes on the cold cache CI always has; with a free key
it is 94 requests and under a minute. The ceiling is sized for the
unauthenticated case so an unset optional secret cannot kill the job.

**T18 is not closed by any of this.** A depositary receipt is deliberately an
equity here: the record describes the right company under the wrong security's
identifier, and OpenFIGI cannot supply the local ISIN that would fix it --
its mapping response carries no ISIN field at all.

## 2026-09-03 Adopt OpenFIGI as an identifier-mapping source

Status: Accepted.

### Decision

`scripts/sources/openfigi.py` may map an identifier -- ISIN to composite FIGI
-- and the result may be stored and republished. It is the fourth source and
the first that supplies no data of its own, only a join. Joining is all it may
do: no field a record publishes may take its *value* from OpenFIGI.

Join on composite FIGI only. **Never join on the ticker OpenFIGI returns**:
Roche's ISIN yields a ticker set whose bare symbols match `RHHVF` and also
Roper Technologies' `ROP`, so a ticker join books Roche's weight into Roper's
sector silently. Measured 2026-09-03, and it is the reason `composite_figis`
exists rather than a general accessor.

### Why

Two problems needed it and neither could be solved from the sources already
here. The sector bridge, T15: N-PORT reports ISIN and CUSIP and never a
ticker -- 1 of 4,857 holdings measured -- while the stock dataset carries 9,400
ISINs and 12,798 CUSIPs against 42,817 composite FIGIs, so the join fails on
identifier shape rather than on missing data. And the identifier defects, T18
and T19: 2,142 published records carry an ISIN whose country disagrees with
their own, FinanceDatabase reports every one of those pairings itself, and
nothing already in the pipeline can tell a correct disagreement from a wrong
one. OpenFIGI can, and did -- it named a different company than the record for
104 of the 164 suspects put to it.

The licence clears, checked 2026-09-03 rather than assumed. FIGI identifiers
carry a Bloomberg public-domain dedication with the MIT licence embedded in the
OMG standard: *"FIGI Identifiers may be freely reproduced, distributed,
transmitted, used, modified, built upon, or otherwise exploited by anyone for
any purpose, commercial or non-commercial"*. No attribution clause, no
non-commercial limit, no restriction on storing or republishing a mapping.
Identifier mapping is neither a quote, a fundamental, nor a proprietary
taxonomy, so neither 2026-05-09 licensing decision reaches it.

### Rejected alternatives

- **GLEIF's ISIN-to-LEI file.** CC0, so the licence is easier still, but it
  bridges only to a legal name and would need fuzzy matching -- which is the
  failure mode being avoided. Second choice if OpenFIGI becomes unavailable.
- **Do nothing and accept the omissions.** T13 omits `sector_weights` on four
  ex-US equity funds, and the cause is measured as an identifier gap rather
  than a data gap: 58.7% of the unresolved weight is holdings matching no
  record, against 0.2% matching a record that carries no sector. Accepting it
  means publishing funds with no sector axis for a reason that is fixable.
- **Add a ticker leg to the join for the holdings FIGI misses.** Rejected on
  the Roche/Roper measurement above. A wrong sector is worse than none, which
  is the same principle the client's P10C package rests on.

### Consequences

`http_cache` gained a POST path, because OpenFIGI's mapping endpoint is
POST-only, and the body now enters the cache key -- which the module docstring
had claimed since before a body could be sent. It also gained
`HOST_MIN_INTERVAL_SEC`, since OpenFIGI allows 25 requests a minute
unauthenticated and the default 1/sec would exceed that twice over.

**Provenance is not settled by this entry and is the open question.** Every
record names source, URL, fetch time and licence, and a record that cannot be
attributed does not ship. A sector reached through OpenFIGI through a
FinanceDatabase record has a two-hop provenance the schema has no shape for.
Nothing may ship on the bridge until that is decided -- see `TASKS.md` T15.

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
