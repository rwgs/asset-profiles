"""Disk-backed, rate-limited HTTP client used by all source modules.

Single shared session per process. Each request is:

  1. Looked up in `.http_cache/{sha256(method:url:body)}` first.
  2. Otherwise fetched, with a 1 req/sec/host token bucket.
  3. robots.txt-checked once per host (cached).
  4. Sent with the SEC-required User-Agent (env: SEC_USER_AGENT).

Used by `sources/finance_database.py`, `sources/edgar.py`,
`sources/issuer_scraper.py`.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
import urllib.robotparser
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

log = logging.getLogger(__name__)

CACHE_DIR = Path(os.environ.get("ASSET_PROFILES_CACHE_DIR", ".http_cache"))

# Deliberately carries no email address. SEC requires one, so this default
# cannot satisfy `_require_sec_contact` and an unset `SEC_USER_AGENT` fails
# loudly on the first EDGAR request rather than sending someone else's contact
# details. It used to name `opensource@wealthfolio.app`, which meant a blank
# secret attributed this fork's traffic to upstream's inbox and the build
# succeeded anyway.
DEFAULT_UA = "asset-profiles dataset builder (https://github.com/rwgs/asset-profiles)"

# SEC's fair-access policy asks that traffic be declared with a real name and a
# working email. It is the only host that requires it, so it is the only host
# the requirement is enforced for.
SEC_HOSTS = frozenset(["sec.gov", "www.sec.gov"])

MIN_INTERVAL_SEC = 1.0  # 1 req/sec/host


def _user_agent() -> str:
    return os.environ.get("SEC_USER_AGENT") or os.environ.get("USER_AGENT") or DEFAULT_UA


def _require_sec_contact(host: str, user_agent: str) -> None:
    """SEC needs a contact address in the User-Agent. Refuse to ask without one.

    Checked against what the session will actually send, not against the
    environment, so a default or a blank secret is caught the same way.
    """
    if host.lower() in SEC_HOSTS and "@" not in user_agent:
        raise RuntimeError(
            f"SEC_USER_AGENT must carry a real name and email before requesting {host}; "
            f"got {user_agent!r}. In CI this is the repository secret of that name."
        )


class _RateLimiter:
    """Per-host token bucket: at most one request per MIN_INTERVAL_SEC seconds."""

    def __init__(self, min_interval: float = MIN_INTERVAL_SEC):
        self._min_interval = min_interval
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, host: str) -> None:
        with self._lock:
            now = time.monotonic()
            prev = self._last.get(host, 0.0)
            wait_for = self._min_interval - (now - prev)
            if wait_for > 0:
                time.sleep(wait_for)
            self._last[host] = time.monotonic()


def check_sec_contact() -> None:
    """Raise unless the configured User-Agent may be used against SEC.

    For a caller that wants to fail before doing any work rather than on the
    first request. `sources.edgar` degrades a failed fetch to an empty mapping
    by design, so without this the ETF pass would resolve no CIK, produce no
    record, and look like a successful stocks-only refresh.
    """
    _require_sec_contact("www.sec.gov", _user_agent())


class HttpCache:
    def __init__(self, cache_dir: Path = CACHE_DIR, *, respect_robots: bool = True):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = _user_agent()
        self.session.headers["Accept-Encoding"] = "gzip, deflate"
        self._rate = _RateLimiter()
        self._robots: dict[str, Optional[urllib.robotparser.RobotFileParser]] = {}
        self._respect_robots = respect_robots

    # ---- public API ----------------------------------------------------

    def get(self, url: str, *, accept: Optional[str] = None, force: bool = False) -> bytes:
        return self._request("GET", url, accept=accept, force=force)

    def get_text(self, url: str, *, encoding: str = "utf-8", **kw) -> str:
        return self.get(url, **kw).decode(encoding, errors="replace")

    def get_json(self, url: str, **kw) -> dict | list:
        return json.loads(self.get_text(url, accept="application/json", **kw))

    # ---- internal ------------------------------------------------------

    def _request(self, method: str, url: str, *, accept: Optional[str], force: bool) -> bytes:
        key = self._cache_key(method, url, accept)
        cache_path = self.cache_dir / key
        if not force and cache_path.exists():
            return cache_path.read_bytes()

        host = urlparse(url).netloc
        # Ahead of the robots check, which fetches robots.txt and is itself a
        # request to the host.
        _require_sec_contact(host, self.session.headers["User-Agent"])

        if self._respect_robots and not self._robots_allows(url):
            raise PermissionError(f"robots.txt disallows {url}")

        self._rate.wait(host)
        headers = {}
        if accept:
            headers["Accept"] = accept
        log.debug("HTTP %s %s", method, url)
        resp = self.session.request(method, url, headers=headers, timeout=60)
        resp.raise_for_status()
        body = resp.content
        cache_path.write_bytes(body)
        return body

    def _cache_key(self, method: str, url: str, accept: Optional[str]) -> str:
        h = hashlib.sha256()
        h.update(method.encode())
        h.update(b"\x00")
        h.update(url.encode())
        if accept:
            h.update(b"\x00")
            h.update(accept.encode())
        return h.hexdigest()

    def _robots_allows(self, url: str) -> bool:
        parts = urlparse(url)
        host = parts.netloc
        if host not in self._robots:
            robots_url = f"{parts.scheme}://{host}/robots.txt"
            rp = urllib.robotparser.RobotFileParser()
            try:
                self._rate.wait(host)
                resp = self.session.get(robots_url, timeout=15)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp = None  # type: ignore[assignment]
            except requests.RequestException:
                log.warning("robots.txt fetch failed for %s; assuming allowed", host)
                rp = None  # type: ignore[assignment]
            self._robots[host] = rp
        rp = self._robots[host]
        if rp is None:
            return True
        return rp.can_fetch(_user_agent(), url)


# Module-level singleton; tests can monkey-patch.
_default: Optional[HttpCache] = None


def default() -> HttpCache:
    global _default
    if _default is None:
        _default = HttpCache()
    return _default
