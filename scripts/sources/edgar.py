"""SEC EDGAR N-PORT loader.

For a given ETF (by ticker or CIK), fetches the most recent N-PORT-P
filing, parses the holdings list, and returns:

    {
      "as_of_date": "2026-04-30",
      "total_value": 530_000_000_000.0,
      "holdings": [
        {
          "name": "Apple Inc.",
          "isin": "US0378331005",
          "cusip": "037833100",
          "ticker": "AAPL",
          "weight": 0.071,
          "value": 37_000_000_000.0,
          "country_code": "US",
          "country": "United States",
          "asset_class": "Equity",
        },
        ...
      ],
    }

Polite by construction: routes through `http_cache.default()` which
enforces 1 req/sec/host with the SEC-required User-Agent.

Raises:
    NotFoundError       — ticker has no CIK or no N-PORT filings
    NotUSDomiciledError — caller should fall back to issuer scraper
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree as ET

from http_cache import default as default_http
from normalize import alpha2_to_country_name

log = logging.getLogger(__name__)


class NotFoundError(Exception):
    pass


class NotUSDomiciledError(Exception):
    pass


# ---- ticker → CIK -------------------------------------------------------

# https://www.sec.gov/files/company_tickers.json
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

_ticker_to_cik_cache: Optional[dict[str, str]] = None


def _ticker_index() -> dict[str, str]:
    global _ticker_to_cik_cache
    if _ticker_to_cik_cache is None:
        try:
            data = default_http().get_json(COMPANY_TICKERS_URL)
        except Exception as e:
            log.warning("failed to fetch company_tickers.json: %s", e)
            _ticker_to_cik_cache = {}
            return _ticker_to_cik_cache
        idx: dict[str, str] = {}
        # Format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "..."}, ...}
        rows = data.values() if isinstance(data, dict) else data
        for row in rows:
            ticker = row.get("ticker")
            cik = row.get("cik_str")
            if ticker and cik is not None:
                idx[ticker.upper()] = f"{int(cik):010d}"
        _ticker_to_cik_cache = idx
        log.info("loaded %d ticker→CIK mappings", len(idx))
    return _ticker_to_cik_cache


def cik_for_ticker(ticker: str) -> Optional[str]:
    return _ticker_index().get(ticker.upper())


# ---- ticker → series ----------------------------------------------------

# https://www.sec.gov/files/company_tickers_mf.json — one row per fund
# share class: [cik, seriesId, classId, symbol]. A trust CIK covers many
# series (iShares Trust files under one CIK for ~400 funds) and each
# N-PORT reports exactly one series, so a CIK on its own does not identify
# a fund's filing.
COMPANY_TICKERS_MF_URL = "https://www.sec.gov/files/company_tickers_mf.json"

_ticker_to_series_cache: Optional[dict[str, tuple[str, str]]] = None


def _series_index() -> dict[str, tuple[str, str]]:
    global _ticker_to_series_cache
    if _ticker_to_series_cache is None:
        try:
            data = default_http().get_json(COMPANY_TICKERS_MF_URL)
        except Exception as e:
            log.warning("failed to fetch company_tickers_mf.json: %s", e)
            _ticker_to_series_cache = {}
            return _ticker_to_series_cache
        idx: dict[str, tuple[str, str]] = {}
        # Format: {"fields": ["cik", "seriesId", "classId", "symbol"],
        #          "data": [[1454889, "S000034163", "C000105320", "SCHD"], ...]}
        fields = data.get("fields", []) if isinstance(data, dict) else []
        for row in data.get("data", []) if isinstance(data, dict) else []:
            rec = dict(zip(fields, row))
            symbol, series, cik = rec.get("symbol"), rec.get("seriesId"), rec.get("cik")
            if symbol and series and cik is not None:
                idx[str(symbol).upper()] = (f"{int(cik):010d}", str(series))
        _ticker_to_series_cache = idx
        log.info("loaded %d ticker→series mappings", len(idx))
    return _ticker_to_series_cache


def series_for_ticker(ticker: str) -> Optional[tuple[str, str]]:
    """(CIK, series ID) for a fund share-class ticker, else None.

    None is the ordinary answer for single-fund filers — SPY, GLD and SLV
    are trusts with no series/class structure, so their CIK already picks
    out a unique filing.
    """
    return _series_index().get(ticker.upper())


# ---- N-PORT filings -----------------------------------------------------


def _filings_index_url(cik: str) -> str:
    return f"https://data.sec.gov/submissions/CIK{cik}.json"


_NPORT_FORMS = ("NPORT-P", "NPORT-P/A")

_SERIES_ID_RE = re.compile(r"SERIES-ID>\s*(S\d{9})")

# Per-CIK scan progress: {"found": {series_id: accession_info}, "next_i": int}.
# Funds sharing a trust resume the walk rather than restarting it, so the
# cost below is paid once per trust, not once per fund.
_series_scan: dict[str, dict] = {}

# Ceiling on headers read per trust. A large trust files a few hundred
# N-PORTs a quarter (iShares Trust covers ~400 funds), so the walk normally
# ends well inside this; the cap only stops a fund that never filed from
# reading the whole submissions history at one request per second.
_MAX_SERIES_SCAN = 600


def _filing_series_ids(cik: str, accession: str) -> set[str]:
    """Series covered by one filing, read from its SGML header.

    The header runs about 3 KB beside a primary_doc.xml that is often
    several MB, so it is the cheap way to tell which fund a filing is for.
    """
    dashed = f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"
    url = f"{_filing_dir_url(cik, accession)}/{dashed}-index-headers.html"
    try:
        body = default_http().get_text(url)
    except Exception as e:
        log.debug("no header for %s/%s: %s", cik, accession, e)
        return set()
    return set(_SERIES_ID_RE.findall(body))


def latest_nport_accession(cik: str, series_id: Optional[str] = None) -> Optional[str]:
    """Accession number (no dashes) of the most recent NPORT-P filing.

    Given `series_id`, returns the most recent filing *for that series*.
    Without it the answer is whichever fund in the trust filed last, which
    is only the right fund when the trust holds exactly one.
    """
    try:
        data = default_http().get_json(_filings_index_url(cik))
    except Exception as e:
        raise NotFoundError(f"no submissions for CIK {cik}: {e}") from e

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accs = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])

    def entry(i: int) -> str:
        acc = accs[i].replace("-", "")
        primary = primary_docs[i] if i < len(primary_docs) else "primary_doc.xml"
        return f"{acc}|{primary}"

    if series_id is None:
        for i, form in enumerate(forms):
            if form in _NPORT_FORMS:
                return entry(i)
        return None

    state = _series_scan.setdefault(cik, {"found": {}, "next_i": 0})
    if series_id in state["found"]:
        return state["found"][series_id]

    # `recent` is newest-first, so the first filing naming a series is that
    # series' latest.
    i = state["next_i"]
    scanned = 0
    while i < len(forms) and scanned < _MAX_SERIES_SCAN:
        if forms[i] in _NPORT_FORMS:
            for sid in _filing_series_ids(cik, accs[i].replace("-", "")):
                state["found"].setdefault(sid, entry(i))
            scanned += 1
            if series_id in state["found"]:
                state["next_i"] = i + 1
                return state["found"][series_id]
        i += 1
    state["next_i"] = i
    log.warning(
        "series %s not found in %d N-PORT filings for CIK %s", series_id, scanned, cik
    )
    return None


def _filing_dir_url(cik: str, accession_no_dashes: str) -> str:
    cik_int = int(cik)
    return f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_no_dashes}"


# ---- N-PORT XML parsing -------------------------------------------------

# N-PORT XML uses namespaces; we strip them on read for simplicity.
def _strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _walk(elem: ET.Element):
    """Yield (local_tag, elem) for every node, namespace-stripped."""
    for child in elem.iter():
        yield _strip_ns(child.tag), child


def _findtext(elem: ET.Element, local_name: str) -> Optional[str]:
    for tag, node in _walk(elem):
        if tag == local_name and node.text is not None:
            return node.text.strip()
    return None


def _to_float(s: Optional[str]) -> Optional[float]:
    if s is None or s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _classify_country(iso: Optional[str], invCountry: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """N-PORT records ISO 3166-1 alpha-2 country codes. Map to display name."""
    code = (iso or invCountry or "").strip().upper()
    if not code:
        return None, None
    if not re.fullmatch(r"[A-Z]{2}", code):
        return None, None
    name = alpha2_to_country_name(code) or code
    return name, code


def _classify_asset(asset_cat: Optional[str]) -> str:
    """N-PORT `assetCat` codes → human label."""
    if not asset_cat:
        return "Other"
    code = asset_cat.upper()
    return {
        "EC":  "Equity",            # Equity-common
        "EP":  "Equity",            # Equity-preferred
        "DBT": "Fixed Income",      # Debt
        "RA":  "Repurchase",
        "DCO": "Commodity Derivative",
        "DE":  "Derivative-equity",
        "DFE": "Derivative-FX",
        "DCR": "Derivative-credit",
        "DIR": "Derivative-rates",
        "STIV": "Cash",             # Short-term investment vehicle
        "ABS-APCP": "Fixed Income",
        "ABS-CBDO": "Fixed Income",
        "ABS-MBS": "Fixed Income",
        "ABS-O": "Fixed Income",
        "LON": "Loan",
        "UST": "Fixed Income",
        "USTBL": "Fixed Income",
        "USTBD": "Fixed Income",
        "USTBN": "Fixed Income",
        "USTSTRIPS": "Fixed Income",
    }.get(code, code if code else "Other")


@dataclass
class NPortHolding:
    name: Optional[str]
    isin: Optional[str]
    cusip: Optional[str]
    ticker: Optional[str]
    value: Optional[float]
    country: Optional[str]
    country_code: Optional[str]
    asset_class: str

    def as_dict(self) -> dict:
        out = {
            "name": self.name,
            "isin": self.isin,
            "cusip": self.cusip,
            "ticker": self.ticker,
            "value": self.value,
            "country": self.country,
            "country_code": self.country_code,
            "asset_class": self.asset_class,
        }
        return {k: v for k, v in out.items() if v is not None}


def _parse_invst_or_sec(node: ET.Element) -> NPortHolding:
    name = _findtext(node, "name") or _findtext(node, "title")
    cusip = _findtext(node, "cusip")
    if cusip and (cusip == "N/A" or cusip.upper().startswith("000000")):
        cusip = None
    isin = None
    ticker = None
    # identifiers block
    for tag, child in _walk(node):
        if tag == "isin":
            isin = (child.get("value") or child.text or "").strip() or None
        elif tag == "ticker":
            ticker = (child.get("value") or child.text or "").strip() or None
    value = _to_float(_findtext(node, "valUSD"))

    iso = _findtext(node, "invCountry")
    country, country_code = _classify_country(iso, iso)

    asset_cat = _findtext(node, "assetCat")
    asset_class = _classify_asset(asset_cat)

    return NPortHolding(
        name=name,
        isin=isin,
        cusip=cusip,
        ticker=ticker,
        value=value,
        country=country,
        country_code=country_code,
        asset_class=asset_class,
    )


def parse_nport_xml(xml_bytes: bytes) -> dict:
    root = ET.fromstring(xml_bytes)

    as_of = None
    total_value = None
    for tag, node in _walk(root):
        if tag == "repPdEnd" and node.text:
            as_of = node.text.strip()
        elif tag == "totAssets" and node.text:
            total_value = _to_float(node.text)

    holdings: list[NPortHolding] = []
    for tag, node in _walk(root):
        if tag in ("invstOrSec", "invstOrSecs"):
            if tag == "invstOrSecs":
                continue  # container
            holdings.append(_parse_invst_or_sec(node))

    # Compute weights
    if total_value and total_value > 0:
        denom = total_value
    else:
        denom = sum((h.value or 0.0) for h in holdings) or 1.0

    out_holdings = []
    for h in holdings:
        d = h.as_dict()
        if h.value is not None:
            d["weight"] = round(h.value / denom, 6)
        out_holdings.append(d)

    return {
        "as_of_date": _normalize_date(as_of),
        "total_value": total_value,
        "holdings": out_holdings,
    }


def _normalize_date(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    # N-PORT uses YYYY-MM-DD already
    try:
        return dt.date.fromisoformat(s[:10]).isoformat()
    except ValueError:
        return None


# ---- public --------------------------------------------------------------


def fetch_latest_nport(cik_or_ticker: str, ticker: Optional[str] = None) -> dict:
    """Fetch + parse the most recent NPORT-P for a fund.

    Accepts either a 10-digit CIK string or a ticker (looked up via
    company_tickers.json). Pass `ticker` alongside a CIK: a trust files one
    N-PORT per series, so the ticker is what picks this fund's filing out
    of its trust's, and it also identifies the trust that actually files
    for the fund when the configured CIK names a different one.
    """
    lookup = ticker or (None if cik_or_ticker.isdigit() else cik_or_ticker)
    series_id = None
    if lookup:
        resolved = series_for_ticker(lookup)
        if resolved:
            series_cik, series_id = resolved
            if cik_or_ticker.isdigit() and cik_or_ticker.zfill(10) != series_cik:
                log.warning(
                    "%s: configured CIK %s does not file series %s; using %s",
                    lookup, cik_or_ticker.zfill(10), series_id, series_cik,
                )
            cik_or_ticker = series_cik

    cik = cik_or_ticker if cik_or_ticker.isdigit() else cik_for_ticker(cik_or_ticker)
    if not cik:
        raise NotFoundError(f"no CIK for {cik_or_ticker!r}")
    cik = cik.zfill(10)

    accession_info = latest_nport_accession(cik, series_id)
    if not accession_info:
        detail = f" series {series_id}" if series_id else ""
        raise NotUSDomiciledError(f"no NPORT-P for CIK {cik}{detail}")

    accession, _primary_hint = accession_info.split("|", 1)
    base = _filing_dir_url(cik, accession)
    # The submissions API often hands back an XSL-styled URL like
    # `xslFormNPORT-P_X01/primary_doc.xml` — that's the rendered view,
    # not the data. Always read the unstyled raw XML.
    body = default_http().get(f"{base}/primary_doc.xml")
    return parse_nport_xml(body)
