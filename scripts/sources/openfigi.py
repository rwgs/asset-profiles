"""OpenFIGI identifier mapping: ISIN -> FIGI records.

The one source here that supplies no data a client classifies on. Two things
come from it: a join, ISIN to composite FIGI, because N-PORT reports ISIN and
CUSIP and never a ticker while the stock dataset is keyed largely on composite
FIGI (`TASKS.md` T15); and an instrument type, which is the only published
field it may set -- see `DECISIONS.md`, where the narrower rule it widened is
recorded next to it.

Licence: FIGI identifiers carry a Bloomberg public-domain dedication with the
MIT licence embedded in the OMG standard. They may be freely reproduced,
distributed and republished, commercially or not, with no attribution clause.
Mapping an identifier is neither a quote, a fundamental, nor a proprietary
taxonomy, so the two 2026-05-09 licensing decisions do not reach it.

Unauthenticated the API allows 25 requests a minute at 10 jobs each. An
`OPENFIGI_API_KEY` raises that to 25 per 6 seconds at 100 jobs, which is the
difference between 39 minutes and under a minute for a sweep of every
published ISIN -- and therefore why the refresh workflow's timeout is 90
minutes rather than 45. A key is optional everywhere: without one the
pacing and batch size simply fall back. The pacing itself lives in
`http_cache.host_min_interval` so it cannot be bypassed here.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Iterable, Optional

from http_cache import HttpCache, default, openfigi_api_key

log = logging.getLogger(__name__)

MAPPING_URL = "https://api.openfigi.com/v3/mapping"
SOURCE_NAME = "OpenFIGI"
SOURCE_URL = "https://www.openfigi.com/"
LICENSE = "Bloomberg FIGI public-domain dedication (MIT)"

# The ceiling on jobs per request. Requesting more is rejected outright rather
# than truncated, so these are hard batch sizes and not tuning knobs: 10
# unauthenticated, 100 with a key.
MAX_JOBS_PER_REQUEST = 10
MAX_JOBS_PER_REQUEST_KEYED = 100


def max_jobs_per_request() -> int:
    return MAX_JOBS_PER_REQUEST_KEYED if openfigi_api_key() else MAX_JOBS_PER_REQUEST


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

    for batch in _batched(wanted, max_jobs_per_request()):
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


# ---- instrument type ----------------------------------------------------

# `securityType2` is the coarse axis and the one worth keying on: measured
# 2026-09-03 over 8,564 published ISINs, every FIGI row for a given ISIN
# agreed on it -- 0 disagreements -- while `securityType` splits the same
# instrument across `EURO-ZONE`, `EURO-DOLLAR`, `EURO MTN` and more.
#
# Anything absent from this table is treated as an equity, so a type OpenFIGI
# adds later leaves records exactly as they are today rather than silently
# restating them as debt. That default is also what keeps `Common Stock`,
# `REIT`, `Preference`, `Preferred Stock`, `Unit`, `Partnership Shares` and
# `Depositary Receipt` equities -- deliberately, in the receipt's case: it
# describes the right company under the wrong security's identifier, which is
# `TASKS.md` T18 and not this rule's business.
_KIND_BY_SECURITY_TYPE2 = {
    # Not equities at all. Bloomberg files structured certificates under
    # `Corp`: `AT0000A2H326` is a leveraged certificate over Daimler and
    # resolves to `ERSTE GROUP BANK AG` / `ERSTBK 0 PERP Z54E`.
    "Corp": "debt",
    "Govt": "debt",
    # Fund shares. They reach the stocks pass because FinanceDatabase's
    # equities file carries them, and they cannot move to `v1/etfs/` because
    # nothing here has their holdings -- see `TASKS.md` T20.
    "Mutual Fund": "fund",
}


def security_kind(records: list[dict]) -> str:
    """Which `kind` the instrument an ISIN identifies should publish as.

    One of `stock`, `fund` or `debt`. Reads the first record's
    `securityType2`, which every row for an ISIN agrees on, and defaults to
    `stock` for a type this table does not name.
    """
    if not records:
        return "stock"
    return _KIND_BY_SECURITY_TYPE2.get(records[0].get("securityType2"), "stock")


def security_names(records: list[dict]) -> list[str]:
    """Every distinct name among a mapping result, in order."""
    return list(dict.fromkeys(r["name"] for r in records if r.get("name")))


# ---- identity check -----------------------------------------------------

# Words that carry no identity: legal forms, share-class and receipt wording.
# Stripping them is what lets "Eaton Vance Municipal Income Trust" and "EVN AG"
# be seen as disjoint while "Alumina Limited" and "ALUMINA LTD" are not.
_NAME_NOISE = frozenset("""
INC INCORPORATED CORP CORPORATION CO COMPANY COMPANIES LTD LIMITED PLC LLC LP
LLP SA SAS SAB CV AG NV BV SE AB AS ASA OYJ OY SPA SRL GMBH KGAA KK JSC PJSC
OJSC PT TBK BHD SDN PCL AD DD OOO PAO OAO ZAO CIA HOLDING HOLDINGS GROUP GRP
THE AND OF CLASS CL SERIES SER ADR ADS GDR GDS SPONSORED SPON UNSPONSORED
SPONS REGS REG SHS SHARES SHARE ORD ORDINARY COMMON STOCK NPV REPRESENTING
NEW UNITS UNIT TRUST FUND REIT
""".split())

# Below this, two tokens are different words rather than spellings of one.
# Measured 2026-09-03 over every published ISIN, and the gap it sits in is
# genuinely narrow. Spelling variants of one name, which must be spared:
# SURGUTNEFTEGAS/SURGUTNEFTEGAZ 0.93, STROER/STROEER 0.92,
# ESSILORLUXOTTICA/ESSILORLUXOT 0.86, ARGENS/ARGENX 0.83. Different companies,
# which must stay flagged: ALEXANDER/ALEXANDERWERK 0.82, AFRICAN/AMERICAN 0.80.
#
# The guard costs two collisions it cannot tell from a misspelling --
# INVACARE/INVOCARE at 0.88 and PACIFICO/PACIFIC at 0.93 -- and that is the
# trade taken deliberately, because the harms are not symmetric: a false
# positive strips a correct ISIN off a correct record, while a false negative
# leaves the record exactly as it publishes today.
_NAME_TOKEN_RATIO = 0.83
_NAME_TOKEN_MIN_LEN = 5


def _name_tokens(name: str) -> set[str]:
    folded = unicodedata.normalize("NFKD", name or "")
    folded = "".join(c for c in folded if not unicodedata.combining(c)).upper()
    return {t for t in re.split(r"[^A-Z0-9]+", folded) if t and t not in _NAME_NOISE}


def _tokens_are_one_spelling(mine: set[str], theirs: set[str]) -> bool:
    """Whether two disjoint token sets are transliterations of one name.

    A German listing writes argenx as `ARGENS` and Stroeer as `STROER`, and a
    FIGI name truncates `ESSILORLUXOTTICA` to `ESSILORLUXOT`. None of those
    shares a token, and every one of them is the same company.
    """
    for a in mine:
        if len(a) < _NAME_TOKEN_MIN_LEN:
            continue
        for b in theirs:
            if len(b) < _NAME_TOKEN_MIN_LEN:
                continue
            if SequenceMatcher(None, a, b).ratio() >= _NAME_TOKEN_RATIO:
                return True
    return False


def names_disagree(record_name: str, figi_names: list[str]) -> bool:
    """Whether OpenFIGI names a different company than the record does.

    Conservative by construction, because acting on this drops a published
    record's canonical key: an empty token set on either side means "cannot
    tell" rather than "different", and one agreeing name among many clears the
    ISIN. See `TASKS.md` T19 for what it is detecting and what it misses.
    """
    mine = _name_tokens(record_name)
    if not mine:
        return False
    for other in figi_names:
        theirs = _name_tokens(other)
        if not theirs:
            return False
        if mine & theirs or _tokens_are_one_spelling(mine, theirs):
            return False
    return bool(figi_names)
