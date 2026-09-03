"""OpenFIGI identifier mapping: ISIN -> FIGI records.

The one source here that supplies no data of its own, only a join. It exists
because N-PORT reports ISIN and CUSIP and never a ticker, while the stock
dataset is keyed largely on composite FIGI -- see `TASKS.md` T15.

Licence: FIGI identifiers carry a Bloomberg public-domain dedication with the
MIT licence embedded in the OMG standard. They may be freely reproduced,
distributed and republished, commercially or not, with no attribution clause.
Mapping an identifier is neither a quote, a fundamental, nor a proprietary
taxonomy, so the two 2026-05-09 licensing decisions do not reach it.

Unauthenticated the API allows 25 requests a minute at 10 jobs each; the pacing
lives in `http_cache.HOST_MIN_INTERVAL_SEC` so it cannot be bypassed here.
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional

from http_cache import HttpCache, default

log = logging.getLogger(__name__)

MAPPING_URL = "https://api.openfigi.com/v3/mapping"
SOURCE_NAME = "OpenFIGI"
SOURCE_URL = "https://www.openfigi.com/"
LICENSE = "Bloomberg FIGI public-domain dedication (MIT)"

# The unauthenticated ceiling on jobs per request. Requesting more is rejected
# outright rather than truncated, so this is a hard batch size and not a tuning
# knob.
MAX_JOBS_PER_REQUEST = 10


def _batched(items: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


def map_isins(
    isins: Iterable[str], *, cache: Optional[HttpCache] = None
) -> dict[str, list[dict]]:
    """Map each ISIN to the FIGI records OpenFIGI holds for it.

    Returns only the ISINs that resolved; one that OpenFIGI has no answer for
    is absent rather than present-and-empty, so a caller cannot mistake "asked
    and got nothing" for "never asked".

    Duplicates and blanks are dropped before batching, and order is preserved,
    so the same input set produces the same requests and therefore the same
    cache keys on a later run.
    """
    http = cache or default()
    wanted = list(dict.fromkeys(i.strip() for i in isins if i and i.strip()))
    out: dict[str, list[dict]] = {}

    for batch in _batched(wanted, MAX_JOBS_PER_REQUEST):
        payload = [{"idType": "ID_ISIN", "idValue": isin} for isin in batch]
        try:
            results = http.post_json(MAPPING_URL, payload)
        except Exception as exc:  # noqa: BLE001 - one bad batch must not end the run
            log.warning("OpenFIGI mapping failed for %d ISINs: %s", len(batch), exc)
            continue
        if not isinstance(results, list) or len(results) != len(batch):
            log.warning(
                "OpenFIGI returned %s results for %d jobs; skipping the batch",
                len(results) if isinstance(results, list) else type(results).__name__,
                len(batch),
            )
            continue
        for isin, result in zip(batch, results):
            data = result.get("data") if isinstance(result, dict) else None
            if data:
                out[isin] = data
    return out


def composite_figis(records: list[dict]) -> list[str]:
    """The composite FIGIs among a mapping result, in order and deduplicated.

    Composite FIGI is the only leg worth joining on. Joining on the ticker
    OpenFIGI returns is a measured mistake: Roche's ISIN yields bare symbols
    matching both `RHHVF` and Roper Technologies' `ROP`, which would book
    Roche's weight into Roper's sector silently. See `TASKS.md` T15.
    """
    figis = [r.get("compositeFIGI") for r in records if r.get("compositeFIGI")]
    return list(dict.fromkeys(figis))
