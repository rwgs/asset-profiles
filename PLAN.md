# Stop a path separator in a shard key creating an unreachable shard

Approach for the change currently in flight: `TASKS.md` **T6**. Replaced when
the next non-trivial change begins, so anything that must outlive this change is
promoted first: decisions that constrain future work to `DECISIONS.md`, and
verified facts that change how the project is understood to `AGENTS.md` or
`SPEC.md`.

T4 held this file before, and its findings are already promoted: the `SAND`
duplicate and the reachability numbers are recorded under `TASKS.md` T4, and the
fact that the gate is now red on `v1/` by design is in `AGENTS.md`.

**No longer blocked.** This waited on #5 so the two would not rewrite
`shard_key` against each other. #5 is merged into `main`, so the function
already has the shape this extends, and the escape character is settled by the
2026-09-02 `DECISIONS.md` entry rather than re-argued here.

## Problem

`shard_key` splits a key on `/`, escapes each component for DOS device names,
and joins the components back with `/`. The join is deliberate in #5 and wrong
here: it means a key containing a separator still returns a path rather than a
filename, and `write_if_changed`'s `mkdir(parents=True)` turns that into a
directory.

FinanceDatabase publishes share classes as `BRK/A`, so `v1/stocks/BRK/A.json` is
written instead of one file. Nine such directories hold 13 records.

T4 already changed what happens next. Before it, those 13 were invisible:
absent from `index.json`, never schema-validated, never reaped. Now the
validator reports all 13, which is why `validate.py v1/` is red. **So this
change is not about finding them any more -- it is about repairing the key so
they stop being created.**

## Approach

One character. `shard_key` joins the escaped components with `_` instead of
`/`, so it returns a single filename component:

```python
return "_".join(_escape_device_name(part) for part in key.split("/"))
```

`BRK/A` becomes `BRK_A`. `CON/A` becomes `CON__A`, because #5's escape runs
first and then the separator escape joins -- one convention composing with
itself, which is why `DECISIONS.md` records `_` for both.

Every one of the 98,464 well-formed keys comes out byte-identical, because no
upstream key contains `/`. That is the property the regression test pins, and it
is the reason the change is one character rather than a migration.

**Report a collision where the keys are collected.** `stock_keys` and
`etf_keys` in `build.py` are sets, so a key already present when the next record
is about to be written is a collision. Log it as an error naming the skipped
record and the key, and skip it, rather than letting `write_if_changed`
overwrite the first record silently.

That guard is for a case that cannot happen today and can happen next week. A
collision needs two upstream keys that differ only in `/` against `_`, and no
key in the current data contains `_` at all -- verified across every stem. But
83,764 of 98,489 shards take their filename straight from an upstream ticker
refreshed weekly, so "no upstream key contains `_`" is a measurement of today's
data, not an invariant. The alternative to the guard is a silent overwrite, and
the whole point of T4 was that this dataset had too many of those.

Nothing else needs to change. The 13 nested records on disk are reaped by the
next build without special handling: their keys become `BRK_A`, so
`v1/stocks/BRK/A.json` matches no current key and T4's recursive `reap_removed`
deletes it.

## Trade-offs

**`BRK_A` and `BRK-A` will both publish, as two records for one security.**
Eleven of the 13 nested keys already have a correct dash-form shard on disk.
This change makes the duplicate visible and addressable instead of hidden in a
directory; it does not resolve it, and resolving it is the same open question
`SAND` raised under T4. Recorded there, not folded in here.

**The gate does not go green.** After this change the 13 nested records still
sit on disk, still unreachable, because a code fix does not rewrite committed
data. `validate.py v1/` still reports 15. That is T5's job and T5 needs sign-off;
what this change buys is that a rebuild would produce a clean tree instead of
recreating the directories.

**Rejected: remove the directories this leaves empty.** Once the nested records
are reaped, nine empty directories remain. Git does not track an empty
directory, so nothing reaches the published tree, and widening what
`reap_removed` may delete for no observable gain is the wrong trade.

**Rejected alternatives for the escape character** -- mapping `/` to `-`, and
percent-encoding -- are settled in `DECISIONS.md` with the measurement that
rules each out. Not re-argued here.

## Verification

**Automated**, in `scripts/tests/test_normalize.py`:

- The five separator keys currently marked `xfail(strict=True)` -- `BRK/A`,
  `BF/A`, `AKO/B`, `RAC/WS`, `BIO/B` -- become plain assertions on the exact
  expected key, not merely on the absence of a separator. They will be reported
  as unexpected passes the moment the fix lands, which is the marker doing its
  job and the signal to tighten them.
- `CON/A` to `CON__A`, asserting the two escapes compose rather than one
  replacing the other. This is the regression the merge ordering existed to
  prevent.
- A regression case over `US0378331005`, `AAPL`, `BRK-A`, `VOD.L` and `CON_.DE`,
  asserting each is returned unchanged. This is the one failure mode that would
  break working clients, so it is pinned on the exact strings.
- Two records escaping to one key, asserting the collision is reported and the
  first record's file is not overwritten.

**Manual:**

- `python scripts/build.py --limit 2000 --out ./probe`, then confirm `probe/`
  contains no directory under `stocks/`. Needs a live FinanceDatabase fetch.
- A `reap_removed` probe over a fixture holding `stocks/BRK/A.json` with
  `BRK_A` as the current key, confirming the nested file is deleted rather than
  left beside its replacement. This is the half a `--limit` build over fresh
  output cannot show, because a fresh `--out` tree has nothing to reap.
