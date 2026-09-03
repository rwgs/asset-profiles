# No change in flight

`TASKS.md` T7 was the last one -- PR #6 merged into `main` with the tests it
owed. This file describes the approach behind the change currently in flight;
there is not one, and saying so is more useful than leaving a finished plan in
place pretending to be current.

Anything from the last change that must outlive it has been promoted already:
the merge and its one conflict-free interaction with `build.py` to `TASKS.md`,
Phase 2 opening and its exit criteria to `ROADMAP.md`, and every measurement to
`TASKS.md` under T7.

## Where the last change left the project

Phase 2 is open. Its headline change is on `main`: two funds sharing a trust now
resolve to their own N-PORT filings, and a configured CIK that does not file the
fund is a logged warning rather than a silent wrong record. The suite is 78
passed, `python scripts/validate.py v1/` still exits 0, and `v1/` is untouched.

Two things are worth carrying into whatever comes next, because both are easy to
misread:

- **The fix is proven against fixtures and not against EDGAR.** The seven new
  tests in `scripts/tests/test_edgar.py` run entirely against a fake HTTP layer,
  so they show that the *selection* is right. They do not show that a real
  `-index-headers.html` matches the regex, that a real multi-megabyte N-PORT
  parses, or that `SCHD`'s holdings are Schwab's. That comparison is still owed
  and needs `SEC_USER_AGENT` set to a real name and email.
- **Nothing in the published data moved, and will not until a refresh runs.**
  The four Schwab records still hold the byte-identical holdings the CIK-level
  lookup produced on 2026-05-31, and `next_refresh_at` is still deliberately
  2026-06-07. Merging a pipeline fix is not refreshing the dataset; a rebuild is
  destructive work needing sign-off, and the refresh half of P2 needs a
  maintainer.

## What the next change needs before it starts

Phase 2 has four items left and `ROADMAP.md` has them. Two are cheap and
self-contained -- rejecting a placeholder `country_code`, and reporting each
universe entry as a record or a named failure -- and two are not: resolving a
holding's sector through CUSIP and ticker as well as ISIN, and omitting a
majority-synthetic weighted list instead of renormalizing `Unknown` to 1.0.

That last one is the only one that changes what the dataset publishes rather
than how it is built, and it is worth noticing that it would take six of the ten
ETF records' `sector_weights` away rather than correct them. Read `SPEC.md` on
absence meaning unknown, and W5 in `TASKS.md`, before starting it.

Two decisions are still open and neither blocks the above, both under `TASKS.md`:

- **The duplicate-record question.** `group_cross_listings` merges by ISIN, so a
  row without one cannot be absorbed. That is one defect behind `SAND`, behind
  the eleven `BRK/A`-style pairs, and behind `BIO/B` and `RAC/WS` now being
  absent rather than repaired. Resolving it settles what the dataset publishes,
  so it is asked rather than implemented.
- **Whether this fork publishes.** Upstream is on standby and `README.md` still
  points jsDelivr at it. If this repository is to serve the client instead, that
  needs `README.md`, the refresh workflow, and a `DECISIONS.md` entry.
