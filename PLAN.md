# No change in flight

`TASKS.md` T5's minimal route and T8 were the last two, and both are committed
on `main`. This file describes the approach behind the change currently in
flight; there is not one, and saying so is more useful than leaving a finished
plan in place pretending to be current.

Anything from the last change that must outlive it has been promoted already:
the escape-character decision to `DECISIONS.md`, the gate now exiting 0 and the
optional issuer extra to `AGENTS.md`, the Phase 1 status to `ROADMAP.md`, and
every measurement to `TASKS.md`.

## Where the last change left the project

`python scripts/validate.py v1/` exits 0, on Windows and under
`-W error::EncodingWarning`, and the suite is 71 passed with no strict markers.
Phase 1 is substantively reached. Two things are worth carrying forward into
whatever comes next, because both are easy to misread:

- **The gate being green is not the dataset being right.** Every record still
  holds data fetched on 2026-05-31, and `next_refresh_at` is deliberately left
  at 2026-06-07 so the dataset keeps reporting its own staleness. Six of the ten
  ETF records still publish a majority fixed-income asset mix for an equity
  fund. The validator was never going to catch that -- Phase 2 is.
- **The pipeline fetches again**, since #1 merged, and a real build is possible
  here for the first time. `build.py --limit 500 --no-etfs --out <probe>` is now
  a cheap way to check a change end to end. Point it at a probe tree, never at
  `v1/`.

## What the next change needs before it starts

Nothing in Phase 1 is left that a fork can do. The next change is a decision
first, and there are two on the page that shape it, both under `TASKS.md`:

- **The duplicate-record question.** `group_cross_listings` merges by ISIN, so a
  row without one cannot be absorbed. That is one defect behind `SAND`, behind
  the eleven `BRK/A`-style pairs, and behind `BIO/B` and `RAC/WS` now being
  absent rather than repaired. Resolving it settles what the dataset publishes,
  so it is asked rather than implemented.
- **Whether this fork publishes.** Upstream is on standby and `README.md` still
  points jsDelivr at it. If this repository is to serve the client instead, that
  needs `README.md`, the refresh workflow, and a `DECISIONS.md` entry.

If the answer is neither yet, Phase 2 is the next outcome and `ROADMAP.md` has
its exit criteria. Its headline change is already written and waiting as #6.
