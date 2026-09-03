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
is `wealthfolio/asset-profiles`. Upstream is what jsDelivr serves and what
`README.md`'s URLs point at, so work here reaches clients only as a pull request
to upstream -- which is how the two open PRs from this fork were sent. A commit
on `origin/main` alone changes nothing any client can see.

**Check the open pull requests before starting work.** Six are open upstream
and they already cover a large part of what `TASKS.md` lists, including the two
worst defects and the test harness. `gh pr list --repo wealthfolio/asset-profiles`, and see the
pull-requests section of `TASKS.md` for the merge order, which is not obvious:
two of them report no conflict with `main` while conflicting with each other.

## Architecture

- `scripts/build.py` is the pipeline entrypoint. It runs a stocks pass, then an
  ETF pass, applies overrides, validates each record, writes shards, and
  rebuilds `v1/index.json` from what survived.
- `scripts/sources/` holds one module per upstream: `finance_database.py`
  (stock rows, MIT), `edgar.py` (SEC N-PORT for US funds, public domain),
  `issuer_scraper.py` (issuer holdings via the `etf-scraper` package, fallback
  for non-US funds only).
- `scripts/normalize.py` turns source rows into schema-shaped records and owns
  `shard_key`, cross-listing merge, weight aggregation, and override merge.
- `scripts/validate.py` is both the CLI gate and the library the build calls
  per record. It enforces JSON Schema plus the weight-sum invariants.
- `scripts/http_cache.py` is the only HTTP path: disk cache under
  `.http_cache/`, one request per second per host, robots.txt honored, and the
  SEC-required User-Agent from `SEC_USER_AGENT`. Do not bypass it.
- `schema/` holds the three JSON Schemas. `config/` holds the ETF universe, the
  Yahoo-suffix-to-MIC map, and the sector label map.
- `manual_overrides/{shard_key}.json` is deep-merged over a generated record
  before validation, so a hand fix survives the weekly rebuild.

`v1/**` is generated. Never hand-edit a shard or `index.json`; change the
source, the normalizer, or an override and rebuild. `v1/` is roughly 400 MB
across about 98,000 files, so glob it rather than reading it whole, and expect
`git status` to be slow.

Toolchain: Python 3.12 in CI, dependencies pinned by lower bound in
`scripts/requirements.txt` and installed with `uv`. Targets are GitHub Actions
`ubuntu-latest` for the build and jsDelivr for delivery. `pytest` covers the
normalizer and the validator; there is no formatter, linter, or type checker
configured.

Windows is a supported development host and the pipeline is not safe on it.
`git clone` fails outright with `invalid path 'v1/stocks/CON.DE.json'` and,
because it fails while building the index, leaves the working tree empty rather
than skipping the record -- so a Windows checkout exists only with the
`core.protectNTFS` check relaxed. PR #5 fixes that, and it is still open.

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

Set up. Python 3.12, with `uv` on PATH. `uv pip install` needs either an active
virtualenv or `--system`; the bare command in `README.md` and `CONTRIBUTING.md`
fails without one. Not 3.13: `etf-scraper` pins `numpy<2.0`, which has no wheel
for 3.13, so the install tries to compile numpy from source and fails. The
tests import neither and run anywhere.

```bash
uv venv
uv pip install -r scripts/requirements.txt
```

Build. `SEC_USER_AGENT` must carry a real name and email or EDGAR answers 403.

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

That command is complete on every host, Windows included. Until #5 merges,
expect three failures on Windows for the two `CON` shards that are named in the
index and absent from the tree.

To check that no new call has started relying on the host locale, make the
warning fatal -- it names the offending line:

```bash
python -X warn_default_encoding -W error::EncodingWarning scripts/validate.py v1/
```

Test. Fast, and it needs only `pycountry` and `jsonschema` from the
requirements, so it runs where a full install does not.

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
has never run against any of the six open ones, so assume a proposed change has
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
