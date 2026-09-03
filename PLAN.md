# One rebuild from closing Phase 2

Nothing is mid-edit. Phase 2's four items are all implemented and `v1/` has been
rebuilt once, at `383fec4aea`. That rebuild predates T13, the last item to land,
so the published tree holds exactly what T13's rule rejects and
`python scripts/validate.py v1/` reports **11 errors**. A second rebuild clears
them and closes the phase.

## What the day delivered

Seven pipeline commits and one data commit, in order:

| Commit | Change |
| --- | --- |
| `790b45e584` | Reject a country code ISO 3166-1 never assigned |
| `b8806b695d` | Resolve a holding's sector through CUSIP |
| `209ddb2343` | Report per-fund ETF coverage from the build |
| `d9bcbd11fd` | Absorb an ISIN-less record whose every symbol is claimed |
| `6e83a572e6` | Publish from this fork; fix URLs that never resolved |
| `61699480e4` | Let a weight express a short position |
| `ebf634d73b` | Omit a weighted list that is mostly unresolved |
| `383fec4aea` | Rebuild `v1/` from the live sources |

The visible result is that `SCHD` describes `SCHD`. It published 98.0% Fixed
Income with the whole Schwab trust's holdings for three months; it now publishes
99.95% Equity, 102 holdings led by QUALCOMM, Texas Instruments and UnitedHealth,
with Health Care at 20.6%. Phase 2 exists for that sentence.

## The next action

**Rebuild again.** It is the same operation as T14, now with a measured cost:
5m48s to build, 59s to validate, about 2m30s to stage and commit. It would omit
`sector_weights` on ten funds and `asset_class_weights` on one, take the gate to
exit 0, and close Phase 2's last exit criterion.

It is a second `v1/**` rewrite, so it needs sign-off like the first. The diff
will be far smaller than T14's: only the 49 ETF records change, plus every
stock record's `provenance.fetched_at`.

## What comes after, and why it is worth doing

**T15, the identifier bridge.** T13 omits `sector_weights` on four ex-US equity
funds -- IEMG, EEM, VWO, VXUS -- and the cause is measured and is not missing
sector data:

- 58.7% of unresolved weight is holdings matching no stock record; 0.2% is
  records carrying no sector.
- The companies are already here. Unmatched holdings against records held for
  the same market: CN 6,189 against 5,992, IN 1,777 against 5,558, JP 1,137
  against 5,110.
- N-PORT reports ISIN and CUSIP and never a ticker -- 1 in 4,857 holdings. The
  dataset carries 9,400 ISINs and 12,798 CUSIPs but **42,817 composite FIGIs**.

So a bridge from holding ISIN to composite FIGI would republish those lists
using sector data already in the dataset. OpenFIGI is the candidate and its
licence must be checked first: `DECISIONS.md` constrains this area, and the fact
that identifier mapping is not quotes, fundamentals or a proprietary taxonomy is
an argument rather than an answer.

## Still owed, and not this project's code

- **`SEC_USER_AGENT` as a repository secret** on `rwgs/asset-profiles`.
  `gh secret list` reports none, and the scheduled refresh takes 403 from EDGAR
  without it. The workflow is committed and correct; the secret is not set.
- **P1**, approving CI on the seven open upstream PRs, needs write access on a
  repository that is on standby.
- **W1 through W7**, the client-side work in `wealthfolio-dev`.

## One trap worth keeping in mind

`build.py --no-stocks` silently produces 100% `Unknown` sector weights, because
the enrichment index comes from the in-memory stocks pass. Under T13 that now
means every `sector_weights` list is omitted rather than merely wrong. A refresh
must never use the flag.
