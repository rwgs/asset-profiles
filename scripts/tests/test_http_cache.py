"""Tests for `scripts/http_cache.py`, the only HTTP path the pipeline has.

`import http_cache` needs `requests`; the rest of this suite deliberately needs
only `pycountry` and `jsonschema`, so skip rather than give that up -- see
`TASKS.md` T8.
"""

from __future__ import annotations

import pytest

pytest.importorskip("requests", reason="http_cache imports requests")

import http_cache  # noqa: E402


# ---- the SEC contact requirement ----------------------------------------
#
# SEC's fair-access policy asks that traffic be declared with a real name and a
# working email. `DEFAULT_UA` used to carry `opensource@wealthfolio.app`, so an
# unset `SEC_USER_AGENT` did not fail -- it attributed this fork's traffic to
# upstream's inbox and the build succeeded. The default now carries no address
# at all, which is what makes the check below unbypassable by accident.


def test_the_default_user_agent_carries_no_email():
    """The structural half of the fix. If this ever gains an `@`, an unset
    secret silently starts passing again."""
    assert "@" not in http_cache.DEFAULT_UA


@pytest.mark.parametrize("host", ["www.sec.gov", "sec.gov", "WWW.SEC.GOV"])
def test_requesting_sec_without_a_contact_is_refused(host):
    with pytest.raises(RuntimeError, match="SEC_USER_AGENT"):
        http_cache._require_sec_contact(host, http_cache.DEFAULT_UA)


def test_requesting_sec_with_a_contact_is_allowed():
    http_cache._require_sec_contact("www.sec.gov", "Some Name some@example.com")


def test_another_host_does_not_need_a_contact():
    """FinanceDatabase is served from GitHub, which asks for no such thing, and
    the stocks pass must keep working without the variable set."""
    http_cache._require_sec_contact("raw.githubusercontent.com", http_cache.DEFAULT_UA)


def test_a_host_that_merely_ends_in_sec_gov_is_not_treated_as_sec():
    """Guard against a substring check: `notsec.gov` is someone else."""
    http_cache._require_sec_contact("notsec.gov", http_cache.DEFAULT_UA)


def test_the_env_var_is_what_supplies_the_contact(monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", "A Person a@example.com")
    assert http_cache._user_agent() == "A Person a@example.com"


def test_a_blank_env_var_falls_back_to_the_default_and_so_is_refused(monkeypatch):
    """The exact misconfiguration this exists for: a repository secret that is
    present but empty."""
    monkeypatch.setenv("SEC_USER_AGENT", "")
    monkeypatch.delenv("USER_AGENT", raising=False)
    ua = http_cache._user_agent()
    assert ua == http_cache.DEFAULT_UA
    with pytest.raises(RuntimeError, match="SEC_USER_AGENT"):
        http_cache._require_sec_contact("www.sec.gov", ua)


def test_the_check_runs_before_robots_is_fetched(tmp_path, monkeypatch):
    """`_robots_allows` fetches robots.txt, which is itself a request to the
    host, so the check has to come first or one request still goes out."""
    monkeypatch.setenv("SEC_USER_AGENT", "")
    monkeypatch.delenv("USER_AGENT", raising=False)
    cache = http_cache.HttpCache(cache_dir=tmp_path)

    def fail(*a, **kw):
        raise AssertionError("a request was made without a contact address")

    monkeypatch.setattr(cache.session, "get", fail)
    monkeypatch.setattr(cache.session, "request", fail)
    with pytest.raises(RuntimeError, match="SEC_USER_AGENT"):
        cache.get("https://www.sec.gov/files/company_tickers.json")


def test_a_cached_response_is_returned_without_the_check(tmp_path, monkeypatch):
    """The requirement is about traffic. Reading a warm cache sends none, so it
    must keep working -- that is what lets the tests and a rebuild run offline."""
    monkeypatch.setenv("SEC_USER_AGENT", "")
    cache = http_cache.HttpCache(cache_dir=tmp_path)
    url = "https://www.sec.gov/files/company_tickers.json"
    (tmp_path / cache._cache_key("GET", url, None)).write_bytes(b'{"cached": true}')
    assert cache.get(url) == b'{"cached": true}'


def test_check_sec_contact_refuses_when_unconfigured(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    monkeypatch.delenv("USER_AGENT", raising=False)
    with pytest.raises(RuntimeError, match="SEC_USER_AGENT"):
        http_cache.check_sec_contact()


def test_check_sec_contact_passes_when_configured(monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", "A Person a@example.com")
    http_cache.check_sec_contact()


# ---- the POST path -------------------------------------------------------
#
# Added for OpenFIGI, whose mapping endpoint is POST-only. The module docstring
# had claimed the cache key hashed the body since before one could be sent;
# `_cache_key` now does, which is what stops two different payloads to the same
# URL sharing an answer.


class _FakeResponse:
    def __init__(self, content: bytes):
        self.content = content
        self.status_code = 200

    def raise_for_status(self):
        pass


def _offline_cache(tmp_path, monkeypatch, content=b'[{"data": []}]'):
    """An HttpCache that records its calls instead of making them."""
    monkeypatch.setenv("SEC_USER_AGENT", "A Person a@example.com")
    cache = http_cache.HttpCache(cache_dir=tmp_path, respect_robots=False)
    calls = []

    def fake_request(method, url, **kw):
        calls.append((method, url, kw))
        return _FakeResponse(content)

    monkeypatch.setattr(cache.session, "request", fake_request)
    monkeypatch.setattr(cache._rate, "wait", lambda host: None)
    return cache, calls


def test_a_post_body_changes_the_cache_key(tmp_path):
    cache = http_cache.HttpCache(cache_dir=tmp_path)
    url = "https://api.openfigi.com/v3/mapping"
    a = cache._cache_key("POST", url, "application/json", b'[{"idValue": "A"}]')
    b = cache._cache_key("POST", url, "application/json", b'[{"idValue": "B"}]')
    assert a != b


def test_a_get_key_is_unchanged_by_the_body_parameter(tmp_path):
    """A warm `.http_cache` must stay valid: adding POST may not move the key
    of any request the pipeline was already making."""
    cache = http_cache.HttpCache(cache_dir=tmp_path)
    url = "https://example.invalid/x.csv"
    assert cache._cache_key("GET", url, None) == cache._cache_key("GET", url, None, None)


def test_post_json_sends_the_bytes_it_hashed(tmp_path, monkeypatch):
    cache, calls = _offline_cache(tmp_path, monkeypatch)
    cache.post_json("https://api.openfigi.com/v3/mapping", [{"idValue": "US0378331005"}])
    (method, url, kw), = calls
    assert method == "POST"
    assert kw["data"] == b'[{"idValue":"US0378331005"}]'
    assert kw["headers"]["Content-Type"] == "application/json"


def test_two_payloads_differing_only_in_key_order_share_one_request(tmp_path, monkeypatch):
    """Sorting the keys is what makes the disk cache hit across runs."""
    cache, calls = _offline_cache(tmp_path, monkeypatch)
    cache.post_json("https://api.openfigi.com/v3/mapping", [{"a": 1, "b": 2}])
    cache.post_json("https://api.openfigi.com/v3/mapping", [{"b": 2, "a": 1}])
    assert len(calls) == 1


def test_a_cached_post_replays_without_a_second_request(tmp_path, monkeypatch):
    cache, calls = _offline_cache(tmp_path, monkeypatch, content=b'[{"data": [1]}]')
    first = cache.post_json("https://api.openfigi.com/v3/mapping", [{"idValue": "X"}])
    second = cache.post_json("https://api.openfigi.com/v3/mapping", [{"idValue": "X"}])
    assert first == second == [{"data": [1]}]
    assert len(calls) == 1


def test_a_different_payload_is_fetched_rather_than_replayed(tmp_path, monkeypatch):
    cache, calls = _offline_cache(tmp_path, monkeypatch)
    cache.post_json("https://api.openfigi.com/v3/mapping", [{"idValue": "X"}])
    cache.post_json("https://api.openfigi.com/v3/mapping", [{"idValue": "Y"}])
    assert len(calls) == 2


def test_a_get_still_sends_no_body(tmp_path, monkeypatch):
    """`data=None` is what requests expects for a bodyless request; passing the
    parameter unconditionally must not turn a GET into one with a body."""
    cache, calls = _offline_cache(tmp_path, monkeypatch)
    cache.get("https://example.invalid/x.csv")
    (method, _, kw), = calls
    assert method == "GET"
    assert kw["data"] is None
    assert "Content-Type" not in kw["headers"]
