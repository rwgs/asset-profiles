"""Tests for `scripts/sources/openfigi.py`, the identifier-mapping source.

`openfigi` imports `http_cache`, which imports `requests`; the rest of this
suite deliberately needs only `pycountry` and `jsonschema`, so skip rather than
give that up -- see `TASKS.md` T8. No test here makes a request.
"""

from __future__ import annotations

import pytest

pytest.importorskip("requests", reason="openfigi imports http_cache")

from sources import openfigi  # noqa: E402


class _FakeHttp:
    """Records the payloads it was asked to POST and replays canned answers."""

    def __init__(self, answers=None, raises=False):
        self.payloads = []
        self._answers = answers or {}
        self._raises = raises

    def post_json(self, url, payload, **kw):
        self.payloads.append(payload)
        if self._raises:
            raise RuntimeError("network is down")
        return [self._answers.get(job["idValue"], {"warning": "No identifier found."})
                for job in payload]


def _hit(name, figi="BBG000000001"):
    return {"data": [{"name": name, "compositeFIGI": figi, "ticker": "X"}]}


def test_an_isin_is_mapped_to_its_records():
    http = _FakeHttp({"US0378331005": _hit("APPLE INC")})
    out = openfigi.map_isins(["US0378331005"], cache=http)
    assert out["US0378331005"][0]["name"] == "APPLE INC"


def test_an_unresolved_isin_is_absent_rather_than_empty():
    """A caller must not be able to confuse 'asked and got nothing' with
    'never asked', which is what an empty list would allow."""
    http = _FakeHttp({})
    assert openfigi.map_isins(["XX0000000000"], cache=http) == {}


def test_the_request_is_batched_to_the_unauthenticated_ceiling():
    http = _FakeHttp({})
    openfigi.map_isins([f"US{i:010d}" for i in range(25)], cache=http)
    assert [len(p) for p in http.payloads] == [10, 10, 5]


def test_jobs_name_the_isin_id_type():
    http = _FakeHttp({})
    openfigi.map_isins(["US0378331005"], cache=http)
    assert http.payloads == [[{"idType": "ID_ISIN", "idValue": "US0378331005"}]]


def test_duplicates_and_blanks_are_dropped_before_batching():
    """Same input set, same requests, so a later run hits the disk cache."""
    http = _FakeHttp({})
    openfigi.map_isins(["A", "A", "", "  ", "B", "A"], cache=http)
    assert [j["idValue"] for j in http.payloads[0]] == ["A", "B"]


def test_input_order_is_preserved():
    http = _FakeHttp({})
    openfigi.map_isins(["C", "A", "B"], cache=http)
    assert [j["idValue"] for j in http.payloads[0]] == ["C", "A", "B"]


def test_a_failed_batch_does_not_end_the_run():
    """One bad batch out of hundreds must cost its own ISINs and no others."""
    http = _FakeHttp({}, raises=True)
    assert openfigi.map_isins(["A", "B"], cache=http) == {}
    assert len(http.payloads) == 1


def test_a_short_response_is_refused_rather_than_misaligned():
    """The API answers positionally. A result list shorter than the job list
    would silently attach one ISIN's answer to another's."""

    class _Misaligned(_FakeHttp):
        def post_json(self, url, payload, **kw):
            self.payloads.append(payload)
            return [_hit("SOMEONE ELSE")]

    http = _Misaligned()
    assert openfigi.map_isins(["A", "B", "C"], cache=http) == {}


def test_composite_figis_are_deduplicated_in_order():
    records = [{"compositeFIGI": "B2"}, {"compositeFIGI": "B1"}, {"compositeFIGI": "B2"}]
    assert openfigi.composite_figis(records) == ["B2", "B1"]


def test_composite_figis_ignores_a_record_without_one():
    assert openfigi.composite_figis([{"ticker": "X"}, {"compositeFIGI": "B1"}]) == ["B1"]


# ---- instrument type ----------------------------------------------------


@pytest.mark.parametrize("security_type2, expected", [
    ("Common Stock", "stock"),
    ("Depositary Receipt", "stock"),   # T18's class: right company, wrong security
    ("REIT", "stock"),
    ("Preference", "stock"),
    ("Partnership Shares", "stock"),
    ("Corp", "debt"),                  # Erste/Raiffeisen structured certificates
    ("Govt", "debt"),
    ("Mutual Fund", "fund"),           # ETP, closed-end and open-end alike
])
def test_security_kind_types_the_instrument(security_type2, expected):
    assert openfigi.security_kind([{"securityType2": security_type2}]) == expected


def test_security_kind_defaults_to_equity():
    """An unmapped or missing type must leave a record as it publishes today."""
    assert openfigi.security_kind([]) == "stock"
    assert openfigi.security_kind([{"securityType2": "Some New Type"}]) == "stock"
    assert openfigi.security_kind([{}]) == "stock"


def test_security_names_dedupes_and_keeps_order():
    records = [{"name": "B"}, {"name": "A"}, {"name": "B"}, {"ticker": "X"}]
    assert openfigi.security_names(records) == ["B", "A"]


# ---- identity check -----------------------------------------------------


@pytest.mark.parametrize("record_name, figi_names", [
    # The two cases `TASKS.md` T19 names, both verified in the published tree.
    ("AAR Corp.", ["CLEAN AIR METALS INC"]),
    ("Eaton Vance Municipal Income Trust", ["EVN AG"]),
    # Others measured 2026-09-03 across `v1/`.
    ("Rayonier Inc.", ["ROYAL BANK OF CANADA"]),
    ("Loews Corporation", ["LOBLAW COMPANIES LTD"]),
    ("THYSSENKRUPP SPONS.ADR 1", ["TELEKOM AUSTRIA AG"]),
    ("Alexander's, Inc.", ["ALEXANDERWERK AG"]),
    ("African Gold Limited", ["AMERICAN AIRLINES GROUP INC"]),
    ("Investigator Resources Limited", ["INVESCO MORTGAGE CAPITAL"]),
])
def test_names_disagree_on_another_companys_isin(record_name, figi_names):
    assert openfigi.names_disagree(record_name, figi_names) is True


@pytest.mark.parametrize("record_name, figi_names", [
    ("Alumina Limited", ["ALUMINA LTD"]),
    # A depositary receipt describes the right company, so it must not be
    # disowned here -- that is T18, and it needs a second identifier source.
    ("Nestle S.A.", ["NESTLE SA-SPONS ADR"]),
    ("Hon Hai Precision Industry Co., Ltd. Sponsored GDR RegS",
     ["HON HAI PRECISION-GDR REG S"]),
    # Transliterations and truncations of one name, all measured in `v1/`.
    ("Surgutneftegas PJSC Reg.Pfd Shs", ["SURGUTNEFTEGAZ-SP ADR PREF"]),
    ("EssilorLuxottica Societe anonyme", ["ESSILORLUXOT-UNSPON ADR"]),
    ("ARGENS SE SP.ADR/1  -,10", ["ARGENX SE - ADR"]),
    ("Stroer SE & Co. KGaA", ["STROEER SE & CO- UNSP ADR"]),
    # One agreeing name among several clears the ISIN.
    ("Carclo plc", ["CAR GROUP LTD", "CARCLO PLC"]),
])
def test_names_agree_or_cannot_tell(record_name, figi_names):
    assert openfigi.names_disagree(record_name, figi_names) is False


@pytest.mark.parametrize("record_name, figi_names", [
    ("", ["ANYTHING INC"]),                  # nothing to compare
    ("Holdings Group Ltd", ["WHATEVER SA"]),  # all noise: no identity either side
    ("Real Name Inc", ["Ltd"]),               # their name is all noise
    ("Real Name Inc", []),                    # never asked
])
def test_names_disagree_is_silent_when_it_cannot_tell(record_name, figi_names):
    """Never guess: this drops a canonical key, so absence of evidence is not evidence."""
    assert openfigi.names_disagree(record_name, figi_names) is False


# ---- a rejected API key -------------------------------------------------


class _Rejecting:
    """Answers every POST the way OpenFIGI answers a bad key."""

    def __init__(self, status):
        self._status = status
        self.payloads = []

    def post_json(self, url, payload, **kw):
        self.payloads.append(payload)
        raise _HttpError(self._status)


class _HttpError(Exception):
    def __init__(self, status):
        super().__init__(f"HTTP {status}")
        self.response = type("R", (), {"status_code": status})()


@pytest.mark.parametrize("status", [401, 403])
def test_a_rejected_key_raises_rather_than_returning_nothing(status, monkeypatch):
    """A bad key fails every batch, so degrading would publish the defects
    both rules exist to correct and still exit 0."""
    monkeypatch.setenv("OPENFIGI_API_KEY", "wrong-value")
    http = _Rejecting(status)
    with pytest.raises(openfigi.CredentialError) as excinfo:
        openfigi.map_isins(["US0378331005"], cache=http)
    assert "OPENFIGI_API_KEY" in str(excinfo.value)
    # Raised on the first batch rather than after sweeping 9,400 ISINs.
    assert len(http.payloads) == 1


@pytest.mark.parametrize("status", [401, 403])
def test_the_same_status_without_a_key_configured_still_degrades(status, monkeypatch):
    """Nothing for the operator to fix, so this keeps the documented posture:
    leave every record as the source reported it and carry on."""
    monkeypatch.delenv("OPENFIGI_API_KEY", raising=False)
    assert openfigi.map_isins(["US0378331005"], cache=_Rejecting(status)) == {}


def test_an_outage_still_degrades_even_with_a_key(monkeypatch):
    """503 is not a credential problem, and OpenFIGI being down must not stop
    a refresh that has real data to publish."""
    monkeypatch.setenv("OPENFIGI_API_KEY", "good-value")
    assert openfigi.map_isins(["US0378331005"], cache=_Rejecting(503)) == {}
