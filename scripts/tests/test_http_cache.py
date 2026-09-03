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
