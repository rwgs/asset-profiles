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
