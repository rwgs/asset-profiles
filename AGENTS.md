# Project instructions

The conventions an agent needs in every session for this repository, loaded
automatically rather than pointed at. Keep it short enough to follow: a rule
earns its place by preventing a repeat mistake or recording durable project
behavior, and reference material belongs under `docs/`.

## Purpose

`asset-profiles` is an open reference dataset of stock and ETF profile data --
sector, industry, country, ETF holdings, and ETF sector/country/asset-class
weights -- published as static JSON over a CDN and rebuilt weekly by GitHub
Actions.

Its consumers are the Wealthfolio clients (desktop, web, mobile), which fetch
records on demand to show allocation, sector, and geographic breakdowns. The
outcome it delivers is that a client can classify a holding without a per-user
API key, a rate limit, or a provider whose terms forbid redistribution. No
integrated Wealthfolio provider yields geographic weights for a fund, which is
the specific gap this dataset exists to close.

This checkout has two remotes: `origin` is `rwgs/asset-profiles` and `upstream`
is `wealthfolio/asset-profiles`. **`origin` is what jsDelivr serves and what
`README.md`'s URLs point at**, decided 2026-09-03 -- see `DECISIONS.md`.
Upstream stays where changes are offered, and every branch stays mergeable
there, but it is no longer what a client fetches.

**Upstream is on standby, stated by its maintainer.** On 2026-09-03 `afadil`
replied on [PR #5](https://github.com/wealthfolio/asset-profiles/pull/5): *"this
repo is not used at all, it was an idea to curate stock and symbol profiles. but
it's en stand by"*. So nothing here reaches a client, no maintainer action in
`TASKS.md` should be expected to happen, and the dataset's staleness is a
property of the project rather than a bug awaiting a merge. Read that before
planning around a merge, a CI approval, or a refresh.

What follows from it, and how work is shaped here:

- **Land work on `origin/main`.** It is the only branch anyone is moving, and it
  is where the harness, the locale fix, and the reachability gate already sit in
  one tree -- which is the only tree where the whole suite runs.
- **Keep a per-task branch that is upstream-mergeable**, cut off `upstream/main`
  or off the branch it genuinely depends on, holding only `scripts/` and the
  documentation the change is about. That is what the seven open PRs are, and
  `fix/unreachable-shard-validation` and `chore/optional-issuer-extra` are two
  waiting without one. If upstream ever comes off standby, they are ready; if
  not, nothing was wasted arranging them.
- **`git checkout upstream/main` fails on Windows**, with
  `error: invalid path 'v1/stocks/CON.DE.json'` -- upstream still carries the
  two unescaped shards that #5 fixes, and `main` is the only branch here that
  has the fix. Git aborts cleanly and leaves `main` intact, so this costs a
  command rather than a checkout. To cut a branch from `upstream/main` anyway,
  build the commit with plumbing instead of a checkout: `read-tree` into a
  temporary `GIT_INDEX_FILE` under `-c core.protectNTFS=false`, `hash-object`
  the files the change touches, then `write-tree` and `commit-tree`. That never
  writes a reserved name to disk and never edits the repository config. Do not
  set `core.protectNTFS=false` persistently to get around it.
- **Do not open more PRs against upstream** without asking. Seven already wait
  on a maintainer who has said they are not working on this, and an eighth
  changes nothing.

**Not every change can have such a branch, and that is a finding rather than an
omission.** T4 has one, `fix/unreachable-shard-validation`, stacked on #8's.
T6 cannot: cut off #5 it would repair the keys but never reap the shards the old
keys nested, because `reap_removed` there is still the one-level glob that T4
replaces. A correct T6 branch needs the stack #5, then #8, then T4, then T6.
`main` is that stack, integrated and gate-verified. Rebuilding it as four
chained pull requests is worth doing if upstream comes off standby, and not
before -- so check `main` for what a change actually depends on before assuming
a branch can be cut from `upstream/main`.

The open PRs still matter as review artifacts and as the record of what is
already written: `gh pr list --repo wealthfolio/asset-profiles`, and see the
pull-requests section of `TASKS.md` for the merge order, which is not obvious --
two of them report no conflict with `main` while conflicting with each other.

## Architecture

- `scripts/build.py` is the pipeline entrypoint. It runs a stocks pass, then an
  ETF pass, applies overrides, validates each record, writes shards, and
  rebuilds `v1/index.json` from what survived.
- `scripts/sources/` holds one module per upstream: `finance_database.py`
  (stock rows, MIT), `edgar.py` (SEC N-PORT for US funds, public domain),
  `issuer_scraper.py` (issuer holdings via the `etf-scraper` package, fallback
  for non-US funds only), and `openfigi.py`, which supplies no
  data a client classifies on -- only an ISIN-to-composite-FIGI join, plus the
  instrument type that sets `kind`. Join on composite FIGI and never on the
  ticker it returns; `DECISIONS.md` has the measurement that rules the ticker
  out, and a second entry for why `kind` is the one published field it may
  set. Never use composite FIGI as evidence about an ISIN in either
  direction: it comes from the same source row as the ISIN, so it is
  contaminated by the defect it would be vouching against.
- `scripts/normalize.py` turns source rows into schema-shaped records and owns
  `shard_key`, cross-listing merge, weight aggregation, and override merge. It
  imports no source module and must stay that way: it is importable with
  `requests` and `pandas` absent, which is what keeps the bare install
  runnable. `apply_instrument_identity` therefore takes plain dicts, and
  `build.figi_identity` is what computes them from OpenFIGI.
- **A record's `kind` is `stock`, `fund` or `debt`**, all three validating
  against `stock.schema.json`. A fund share or a structured note reaches the
  stocks tree because FinanceDatabase publishes them among equities, and both
  omit `sector`, which they do not have. Only `etf` has a schema of its own,
  because only it carries holdings.
- `scripts/validate.py` is both the CLI gate and the library the build calls
  per record. It enforces JSON Schema plus the weight-sum invariants.
- `scripts/http_cache.py` is the only HTTP path: disk cache under
  `.http_cache/`, one request per second per host unless
  `host_min_interval()` names a slower one, robots.txt honored, and the
  SEC-required User-Agent from `SEC_USER_AGENT`. Do not bypass it. `post_json`
  exists for OpenFIGI, whose endpoint is POST-only; it hashes the request body
  into the cache key, so a new POST caller gets caching for free and two
  payloads to one URL can never share an answer. A request to
  `sec.gov` without a contact address in the User-Agent raises rather than
  falling back to a default, and `build.py` makes the same check up front so a
  missing one costs five seconds instead of a wrong dataset. It also reads an
  optional `OPENFIGI_API_KEY`, which is sent as a header and deliberately kept
  out of the cache key -- the key identifies the caller, not the question, so
  configuring one must not discard a warm cache. It is worth having: typing
  every published ISIN is 940 requests and about 39 minutes without it, and 94
  requests and under a minute with it, because the tier raises both the pacing
  and the jobs per request. **A key that is set and rejected exits 2**, on the
  same grounds as the SEC check: it fails every batch, so degrading would
  publish the defects T19 and T20 exist to correct and still exit 0. A bad key
  is worse than no key, since unset simply means batches of 10. Any other
  OpenFIGI failure -- an outage, a 503 -- still degrades and leaves each record
  as the source reported it.
- `schema/` holds the three JSON Schemas. `config/` holds the ETF universe, the
  Yahoo-suffix-to-MIC map, and the sector label map.
- `manual_overrides/{shard_key}.json` is deep-merged over a generated record
  before validation, so a hand fix survives the weekly rebuild.

`v1/**` is generated. Never hand-edit a shard or `index.json`; change the
source, the normalizer, or an override and rebuild. `v1/` is roughly 90,600
files, so glob it rather than reading it whole, and expect git to be slow.

Measured twice on 2026-09-03, and the difference is the lesson: `git add -A v1/`
after a rebuild took **1m43s** on an otherwise idle disk and **13m41s** while a
build and several test runs competed for the same one. Start it, then leave the
disk alone -- it is I/O bound, not stuck. The commit itself is about thirty
seconds either way. A `git add` that is killed part-way leaves a stale, empty
`.git/index.lock`; the editor's git integration then fails against it
repeatedly, which looks like the cause and is not. Confirm no live `git`
process holds it -- CPU time still climbing means it is working -- before
removing it.

A full rebuild is **about seven minutes** on a developer host -- 5m48s to build
and 59s to validate, measured 2026-09-03 with a warm `.http_cache`. Cold, the
ETF pass costs about eleven minutes more at one request per second, and the
stocks pass now costs an OpenFIGI sweep of every published ISIN on top: about
39 minutes unauthenticated, under a minute with `OPENFIGI_API_KEY`. The
refresh workflow's timeout is 90 minutes because of it, sized for the
unauthenticated case so an unset optional secret cannot kill the job.

Toolchain: Python 3.12 in CI, dependencies pinned by lower bound in
`scripts/requirements.txt` and installed with `uv`. The non-US issuer fallback
is the one exception, split into `scripts/requirements-issuer.txt` because it
pins `numpy<2.0` and would otherwise cap the whole project at 3.12. Targets are GitHub Actions
`ubuntu-latest` for the build and jsDelivr for delivery. `pytest` covers the
normalizer, the validator, the build's write-and-reap loop and coverage report,
and EDGAR's series-level filing selection and country classification; there is
no formatter, linter, or type checker configured.

**Windows is a supported development host and the repository now clones on it.**
PR #5's escaping is merged to `main`, so this is fixed rather than worked
around. Verified 2026-09-02 by cloning `main` with `core.protectNTFS` left at
its default: the clone completed, `git status` was clean, no path carried
`skip-worktree`, and all 98,464 stock shards were on disk -- the same count a
Linux checkout gets. `validate.py v1/` then reported the same errors there as on
Linux -- 15 at the time, then zero, and 4 since T9 -- and the suite the same
count.

If you are in an older checkout, `core.protectNTFS=false` and `skip-worktree` on
`v1/stocks/CON.json` and `v1/stocks/CON.DE.json` were the workaround. Clear them
and re-clone; they are no longer needed and `git ls-files -v v1/stocks/` should
now print `H` for every path.

Worth knowing, because it is easy to blame the wrong layer: it was **git** that
refused these names, not the OS. `core.protectNTFS` rejects a path whose
component looks like an NTFS device name, which is why the clone died on
`invalid path 'v1/stocks/CON.DE.json'` while building the index and left the
tree empty. Measured on this host, Windows 11 itself creates `CON.json` without
complaint. So the defect was real and the fix is right -- git is what every
contributor goes through -- but do not expect a bare `open("CON.json")` to fail
when reasoning about it.

The locale half is fixed: every `read_text()` in `scripts/` names its encoding
and the validator reports in ASCII, so the gate runs on a cp1252 host with no
environment overrides. Keep it that way -- a bare `read_text()` or a non-ASCII
character in a message the validator writes itself puts it back.

## Working boundaries

- Leave unrelated changes exactly as found. Every changed line traces to
  something the request asked for, so raise a simpler approach or an unrelated
  defect rather than acting on it.
- Make the smallest change that solves the stated problem. Add no speculative
  feature, abstraction for a single call site, configuration knob, or handling for
  a case that cannot occur.
- Match the naming, layout, and style already in the file, even where a different
  approach would be the better call in a new project.
- Remove what the change orphans, such as an import nothing uses. Leave
  pre-existing dead code alone unless asked to remove it, and mention it where it
  matters.
- Never commit or print credentials, sessions, private data, or environment
  files.
- Ask before destructive work. Deleting, overwriting, resetting, force-pushing,
  migrating, and deploying are not implied by a request to fix something.
  Rewriting `v1/**` counts: it is a 98,000-file diff no reviewer can read, so a
  pipeline change and the data rebuild it causes are separate commits.
- Ask before a change that settles a product or architecture question, rather
  than implementing one already settled.
- Never add data derived from Yahoo Finance, and never add quotes, OHLCV,
  fundamentals, or analyst data from anywhere. Never use a proprietary
  taxonomy's name; use the labels in `config/sector_taxonomy.yml`. These are
  licensing boundaries, not preferences -- see `DECISIONS.md`.
- Every record carries a `provenance` block naming source, URL, fetch time, and
  license. A record that cannot be attributed does not ship.

## Before editing

- State the plan, or what success looks like, before editing, as a check that can
  fail rather than a description: the test that reproduces the bug, the test for
  the input that must be rejected, the same tests passing either side of a
  refactor. Pair each step of multi-step work with the check that confirms it.
- Stop at any ambiguity in the request, before editing anything. Name what is
  unclear and the readings it admits, and wait for an answer rather than picking
  one silently or proceeding on the likeliest reading.
- An unread fact is not an ambiguity. Read the code or run the command that
  settles it, and state any assumption that changes the result.
- Say when a simpler approach than the one asked for would do, and challenge a
  wrong premise before building on top of it.
- A claim about the data is a measurement, not a reading of the pipeline. The
  code that reads correctly is currently recording an equity fund as 98% fixed
  income, so open the shard before trusting the module that wrote it.

## Commands

Set up. Any supported Python, with `uv` on PATH. `uv pip install` needs either
an active virtualenv or `--system`; the bare command in `README.md` and
`CONTRIBUTING.md` fails without one.

```bash
uv venv
uv pip install -r scripts/requirements.txt
```

**The version ceiling is gone from that command, and only from that command.**
`etf-scraper` pins `numpy<2.0`, which publishes no wheel past 3.12, so the
install used to compile numpy from source and fail on any host without a C
toolchain. It now lives in `scripts/requirements-issuer.txt` and is installed
separately -- verified 2026-09-03 by installing the rest on Python 3.14.5 and
running a live build. CI still pins 3.12 and still installs the extra, so what
the refresh produces has not changed.

```bash
uv pip install -r scripts/requirements-issuer.txt    # non-US issuer fallback
```

Skip it unless you are working on `issuer_scraper.py`. The import is lazy and
the build reports a named failure and continues without it, which is already
what happens for every fund reaching that path -- all ten published ETF records
come from EDGAR and none from the scraper.

Build. `SEC_USER_AGENT` must carry a real name and email, or the build exits 2
before doing any work. `--no-etfs` does not need it.

```bash
SEC_USER_AGENT="your-name your@email" python scripts/build.py
SEC_USER_AGENT="your-name your@email" python scripts/build.py --no-etfs
SEC_USER_AGENT="your-name your@email" python scripts/build.py --no-stocks
python scripts/build.py --limit 500 --out ./probe    # debug, small output tree
```

Validate. This is the whole gate, and it takes about a minute over `v1/`.

```bash
python scripts/validate.py v1/
```

That command is complete on every host, and as of 2026-09-03 it **exits 0** on
all of them, against a `v1/` rebuilt the same day. Treat any failure as
something your change caused.

The count has been red three times and each time it was the design working:
T4's 15, T9's 4, and T13's 11. None was cleared by editing a shard -- two by a
rebuild and one by the fix that caused it. If you make the gate red, say which
of those two it is.

It reported 15 errors for a day and the history is worth knowing, because the
number appears in `TASKS.md` and in commit messages: T4 made an unreachable
shard a failure, which surfaced the 13 records the old `shard_key` had nested
under directories plus `stocks/SAND.json`, and a three-way count mismatch. T6
stopped new ones being created and the minimal half of T5 retired the 14. The
gate going red was the design working, not a regression.

**A red gate on `v1/` is a real result, so do not rebuild the data to clear
it without sign-off.** Deleting or regenerating shards is destructive work; see
the working boundaries above. A rebuild is the right answer often enough that
the rule is worth stating precisely: it is what cleared T9's 4 and T13's 11,
both times as a separate commit holding nothing but `v1/**`, and both times
after being rehearsed into a `--out` tree first.

To check that no new call has started relying on the host locale, make the
warning fatal -- it names the offending line:

```bash
python -X warn_default_encoding -W error::EncodingWarning scripts/validate.py v1/
```

Test. Fast, and it needs only `pycountry` and `jsonschema` from the
requirements, so it runs where a full install does not. `test_build.py`,
`test_edgar.py`, `test_http_cache.py` and `test_openfigi.py` `importorskip` on
`pandas` or `requests`, so on that bare install they skip rather than fail:
measured 2026-09-03, **111 passed and 4 skipped** with only `pytest`,
`pycountry` and `jsonschema` installed, against **221 passed** with the full
requirements. CI installs everything, so nothing is skipped on the runner.

```bash
python -m pytest scripts/tests
```

A `shard_key` case marked `xfail(strict=True)` is a defect the suite knows
about and the code has not fixed yet. When the fix lands, pytest reports it as
an unexpected pass: turn it into a plain assertion in the same change rather
than dropping the marker.

There is no `lint`, `fmt`, or `typecheck` command. Do not invent one inside a
change that needs it; adding the harness is its own task.

`validate-pr.yml` is gated behind maintainer approval for fork pull requests and
has never run against any of the seven open ones, so assume a proposed change
been reviewed and not checked.

## Validation

- Run the focused check while implementing: `python -m pytest scripts/tests`,
  and `validate.py` against a small `--out` tree rather than against `v1/`.
- Run the complete required local gate before reporting done:
  `python -m pytest scripts/tests` and `python scripts/validate.py v1/`.
- Inspect the final status and diff, and confirm every changed line traces to
  something the task asked for.
- Verify visible behavior by reading the shard the change was meant to affect
  and comparing it against the filing or page it came from. A passing validator
  is not evidence the data is right: the weight-sum invariant is satisfied by
  construction, because unknown values are bucketed as `Unknown` and then
  renormalized to 1.0.
- Report skipped checks and outstanding manual testing rather than omitting
  them.

## Documentation routing

- `SPEC.md` for requirements and acceptance criteria.
- `ROADMAP.md` for phase order and exit criteria.
- `TASKS.md` for current work and validation status, including the work this
  dataset owes the `wealthfolio-dev` client.
- `PLAN.md` for the approach behind the change currently in flight.
- `DECISIONS.md` before changing an area it constrains, and before proposing an
  approach it already rejected.
- `docs/asset-profiles-spec.md` is the original design spec, dated 2026-05-09
  and still marked *Proposed*. Read it for intended shapes the code has not
  reached; where it and `SPEC.md` disagree, `SPEC.md` is current.
- `README.md` is where a human or an agent arriving cold starts, and it owns none
  of the above. It links to these documents, and to the files it describes,
  rather than restating them: an explanation kept away from what it explains
  drifts from it silently.
