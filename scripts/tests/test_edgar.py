"""Tests for `scripts/sources/edgar.py`'s series-level filing selection.

`from sources import edgar` pulls in `http_cache`, and through it `requests`.
The rest of this suite deliberately needs only `pycountry` and `jsonschema`, so
that it runs on a host where the full requirements do not install -- see
`TASKS.md` T8. Skip rather than give that up, as `test_build.py` does.

Everything below runs against a fake HTTP layer holding one trust that files
for two funds. That is the shape the defect lives in: 42 of the 65 universe
entries share a CIK with another entry, so a CIK on its own cannot tell them
apart.
"""

from __future__ import annotations

import json
import logging

import pytest

pytest.importorskip("requests", reason="edgar.py imports http_cache")

from sources import edgar  # noqa: E402

# Select Sector SPDR Trust, which files for all eleven sector funds.
TRUST_CIK = "0001064641"
# SPDR Series Trust -- a different filer, and what `config/etf_universe.yml`
# names for these funds today. One of the 19 wrong CIKs PR #6 found.
CONFIGURED_CIK = "0001064642"

XLF_SERIES = "S000000001"
XLK_SERIES = "S000000002"

# Newest first, as the submissions API returns them: XLK filed last, so it is
# the filing a CIK-level lookup finds for every fund in the trust.
XLK_ACCESSION = "000106464126000009"
XLF_ACCESSION = "000106464126000008"


def _nport_xml(as_of: str, name: str, ticker: str) -> bytes:
    """The smallest N-PORT `parse_nport_xml` reads a holding out of."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/nport">
  <formData>
    <genInfo><repPdEnd>{as_of}</repPdEnd></genInfo>
    <fundInfo><totAssets>1000.0</totAssets></fundInfo>
    <invstOrSecs>
      <invstOrSec>
        <name>{name}</name>
        <identifiers><ticker value="{ticker}"/></identifiers>
        <valUSD>250.0</valUSD>
        <invCountry>US</invCountry>
        <assetCat>EC</assetCat>
      </invstOrSec>
    </invstOrSecs>
  </formData>
</edgarSubmission>
""".encode()


def _submissions(cik: str, rows: list[tuple[str, str, str]]) -> bytes:
    """The `filings.recent` shape, as three parallel arrays newest-first."""
    return json.dumps(
        {
            "cik": cik,
            "filings": {
                "recent": {
                    "form": [r[0] for r in rows],
                    "accessionNumber": [r[1] for r in rows],
                    "primaryDocument": [r[2] for r in rows],
                }
            },
        }
    ).encode()


def _dashed(accession: str) -> str:
    return f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"


def _filing_url(cik: str, accession: str, leaf: str) -> str:
    """Built here rather than through `edgar`'s own helpers, so the test pins
    the URL shape instead of agreeing with whatever the code produces."""
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{leaf}"


def _header_url(cik: str, accession: str) -> str:
    return _filing_url(cik, accession, f"{_dashed(accession)}-index-headers.html")


def _headers_html(*series_ids: str) -> bytes:
    """An SGML header carries one SERIES-ID per series the filing covers."""
    body = "".join(
        f"<SERIES-ID>{sid}\n<CLASS-CONTRACT-ID>C00000000{i}\n"
        for i, sid in enumerate(series_ids)
    )
    return (
        "<SEC-HEADER>\n<SERIES-AND-CLASSES-CONTRACTS-DATA>\n"
        f"{body}</SEC-HEADER>"
    ).encode()


MF_ROWS = {
    "fields": ["cik", "seriesId", "classId", "symbol"],
    "data": [
        [1064641, XLF_SERIES, "C000000001", "xlf"],
        [1064641, XLK_SERIES, "C000000002", "XLK"],
    ],
}


def _bodies() -> dict[str, bytes]:
    return {
        edgar.COMPANY_TICKERS_MF_URL: json.dumps(MF_ROWS).encode(),
        f"https://data.sec.gov/submissions/CIK{TRUST_CIK}.json": _submissions(
            TRUST_CIK,
            [
                ("N-CEN", "0001064641-26-000010", "primary_doc.xml"),
                # The submissions API often names the XSL-styled view here.
                ("NPORT-P", _dashed(XLK_ACCESSION), "xslFormNPORT-P_X01/primary_doc.xml"),
                ("NPORT-P", _dashed(XLF_ACCESSION), "primary_doc.xml"),
            ],
        ),
        _header_url(TRUST_CIK, XLK_ACCESSION): _headers_html(XLK_SERIES),
        _header_url(TRUST_CIK, XLF_ACCESSION): _headers_html(XLF_SERIES),
        _filing_url(TRUST_CIK, XLK_ACCESSION, "primary_doc.xml"): _nport_xml(
            "2026-04-30", "Microsoft Corporation", "MSFT"
        ),
        _filing_url(TRUST_CIK, XLF_ACCESSION, "primary_doc.xml"): _nport_xml(
            "2026-01-31", "JPMorgan Chase and Co.", "JPM"
        ),
    }


class FakeHttp:
    """The slice of `http_cache.HttpCache` edgar uses, layered the same way:
    `get_text` and `get_json` derive from `get`, so a test registers bytes and
    gets all three."""

    def __init__(self, bodies: dict[str, bytes]):
        self.bodies = bodies
        self.requested: list[str] = []

    def get(self, url: str, **kw) -> bytes:
        self.requested.append(url)
        if url not in self.bodies:
            raise AssertionError(f"unregistered URL: {url}")
        return self.bodies[url]

    def get_text(self, url: str, *, encoding: str = "utf-8", **kw) -> str:
        return self.get(url, **kw).decode(encoding, errors="replace")

    def get_json(self, url: str, **kw):
        return json.loads(self.get_text(url, **kw))


@pytest.fixture
def http(monkeypatch):
    """A fake HTTP layer, with edgar's three module caches cleared. They are
    process-global memos, so without this a test would see what ran before it."""
    monkeypatch.setattr(edgar, "_ticker_to_series_cache", None)
    monkeypatch.setattr(edgar, "_ticker_to_cik_cache", None)
    monkeypatch.setattr(edgar, "_series_scan", {})
    fake = FakeHttp(_bodies())
    monkeypatch.setattr(edgar, "default_http", lambda: fake)
    return fake


def _tickers(result: dict) -> list[str]:
    return [h.get("ticker") for h in result["holdings"]]


def test_two_funds_in_one_trust_get_their_own_filing(http):
    """Phase 2's headline exit criterion, at the unit level. Both funds file
    under one CIK, so before the series lookup both resolved to whichever of
    them filed last and the two records came out byte-identical."""
    xlk = edgar.fetch_latest_nport(TRUST_CIK, ticker="XLK")
    xlf = edgar.fetch_latest_nport(TRUST_CIK, ticker="XLF")

    assert _tickers(xlk) == ["MSFT"]
    assert _tickers(xlf) == ["JPM"]
    assert xlk["as_of_date"] == "2026-04-30"
    assert xlf["as_of_date"] == "2026-01-31"


def test_without_a_ticker_the_trusts_newest_filing_wins(http):
    """The documented single-fund behavior, kept for SPY, DIA, GLD and SLV,
    whose filers have no series structure. It is also the defect above: asked
    for the trust alone, EDGAR answers with XLK's filing whatever fund the
    caller meant."""
    assert _tickers(edgar.fetch_latest_nport(TRUST_CIK)) == ["MSFT"]


def test_the_header_walk_is_shared_by_the_funds_in_a_trust(http):
    """The scan resumes where the previous fund left it rather than restarting,
    which is what keeps an eleven-fund trust from re-reading the same headers
    eleven times at one request per second."""
    edgar.fetch_latest_nport(TRUST_CIK, ticker="XLK")
    edgar.fetch_latest_nport(TRUST_CIK, ticker="XLF")

    header_reads = [u for u in http.requested if u.endswith("-index-headers.html")]
    assert sorted(header_reads) == sorted(
        [_header_url(TRUST_CIK, XLK_ACCESSION), _header_url(TRUST_CIK, XLF_ACCESSION)]
    ), "a header was read twice, so the per-trust scan restarted"


def test_a_fund_that_never_filed_is_reported_rather_than_given_anothers_filing(
    http, caplog
):
    """The failure mode worth having: no filing for this series is an error the
    build records, not a silently plausible record built from a sibling fund."""
    edgar._series_index()["XLY"] = (TRUST_CIK, "S000000009")

    with caplog.at_level(logging.WARNING):
        with pytest.raises(edgar.NotUSDomiciledError, match="S000000009"):
            edgar.fetch_latest_nport(TRUST_CIK, ticker="XLY")

    assert "S000000009" in caplog.text


def test_a_configured_cik_that_does_not_file_the_series_is_overridden_and_logged(
    http, caplog
):
    """19 of the 52 configured US CIKs name a filer that does not file the
    fund. Deriving the filer from SEC's own mapping makes that a logged warning
    rather than a wrong record -- here the configured CIK has an N-PORT of its
    own, so failing to override would produce a plausible decoy."""
    http.bodies[f"https://data.sec.gov/submissions/CIK{CONFIGURED_CIK}.json"] = (
        _submissions(
            CONFIGURED_CIK,
            [("NPORT-P", "0001064642-26-000001", "primary_doc.xml")],
        )
    )
    http.bodies[
        _filing_url(CONFIGURED_CIK, "000106464226000001", "primary_doc.xml")
    ] = _nport_xml("2026-04-30", "Decoy Holding", "DECOY")

    with caplog.at_level(logging.WARNING):
        result = edgar.fetch_latest_nport(CONFIGURED_CIK, ticker="XLF")

    assert _tickers(result) == ["JPM"]
    assert CONFIGURED_CIK in caplog.text and XLF_SERIES in caplog.text


def test_the_series_index_pads_the_cik_and_ignores_ticker_case(http):
    """`company_tickers_mf.json` carries the CIK as a bare integer, while every
    URL edgar builds wants it zero-padded to ten."""
    assert edgar.series_for_ticker("XLF") == (TRUST_CIK, XLF_SERIES)
    assert edgar.series_for_ticker("xlk") == (TRUST_CIK, XLK_SERIES)
    assert edgar.series_for_ticker("SPY") is None


def test_an_unreadable_series_index_leaves_the_cik_path_working(http, caplog):
    """The mapping is one more SEC endpoint that can fail. When it does, every
    fund should degrade to the pre-existing CIK-level answer rather than fail
    the ETF pass outright."""
    http.bodies[edgar.COMPANY_TICKERS_MF_URL] = b"<html>503</html>"

    with caplog.at_level(logging.WARNING):
        assert edgar.series_for_ticker("XLF") is None
        assert _tickers(edgar.fetch_latest_nport(TRUST_CIK, ticker="XLF")) == ["MSFT"]

    assert "company_tickers_mf.json" in caplog.text
