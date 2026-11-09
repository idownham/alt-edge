"""Paced, unauthenticated HTTP GETs. Read-only; no keys are ever sent.

Limits (HQ `../CLAUDE.md`, shared resources):
- Kalshi public REST: <= 1 request/s, 10 s back-off on HTTP 429.
- rollcall.com (Factbase): <= 1 page / 2 s, every page cached on disk and fetched once.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "bloodhound-research/0.1 (read-only class research; paced)"


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class PacedClient:
    """Enforces a minimum interval between requests and backs off on 429."""

    def __init__(self, min_interval_s: float, backoff_429_s: float = 10.0, max_tries: int = 6,
                 sleep=time.sleep, clock=time.monotonic):
        self.min_interval_s = min_interval_s
        self.backoff_429_s = backoff_429_s
        self.max_tries = max_tries
        self._sleep = sleep
        self._clock = clock
        self._last = None
        self.requests_made = 0

    def _pace(self) -> None:
        if self._last is not None:
            wait = self.min_interval_s - (self._clock() - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._clock()

    def _open(self, url: str) -> tuple[int, bytes]:  # separated for tests
        # curl uses the system trust store (python.org's macOS build has no CA bundle by default).
        p = subprocess.run(["curl", "-sS", "-m", "60", "-A", USER_AGENT, "-H", "Accept: */*",
                            "-w", "\n%{http_code}", url], capture_output=True)
        if p.returncode != 0:
            raise ConnectionError(p.stderr.decode(errors="replace")[:200])
        body, _, code = p.stdout.rpartition(b"\n")
        return int(code), body

    def get_bytes(self, url: str) -> bytes:
        for attempt in range(self.max_tries):
            self._pace()
            self.requests_made += 1
            try:
                code, body = self._open(url)
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                print(f"network error {e!r}; retry in {self.backoff_429_s}s", file=sys.stderr)
                self._sleep(self.backoff_429_s)
                continue
            if code == 429:
                print(f"429 from {urllib.parse.urlsplit(url).netloc}; backing off {self.backoff_429_s}s",
                      file=sys.stderr)
                self._sleep(self.backoff_429_s)
                continue
            if code >= 500:
                self._sleep(self.backoff_429_s)
                continue
            if code != 200:
                raise HTTPStatusError(code, url, body[:300])
            return body
        raise RuntimeError(f"gave up after {self.max_tries} tries: {url}")


class HTTPStatusError(RuntimeError):
    def __init__(self, code: int, url: str, body: bytes):
        super().__init__(f"HTTP {code} for {url}: {body!r}")
        self.code = code


class KalshiPublic:
    BASE = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self, client: PacedClient | None = None):
        self.client = client or PacedClient(min_interval_s=1.05)

    def get(self, path: str, **params) -> dict:
        q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{self.BASE}{path}" + (f"?{q}" if q else "")
        return json.loads(self.client.get_bytes(url))


class CachedPages:
    """Fetch-once disk cache for rollcall.com pages (Q4: cached locally, not redistributed)."""

    def __init__(self, cache_dir: Path, client: PacedClient | None = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.client = client or PacedClient(min_interval_s=2.0)

    def path_for(self, url: str) -> Path:
        slug = urllib.parse.urlsplit(url).path.strip("/").replace("/", "__")[-120:]
        return self.cache_dir / f"{slug}__{hashlib.sha1(url.encode()).hexdigest()[:8]}.html"

    def get(self, url: str, refresh: bool = False) -> tuple[str, str]:
        """Return (html, fetched_utc). Cached pages are not re-fetched unless refresh=True."""
        p = self.path_for(url)
        meta = p.with_suffix(".meta.json")
        if p.exists() and not refresh:
            fetched = json.loads(meta.read_text())["fetched_utc"] if meta.exists() else "unknown"
            return p.read_text(), fetched
        body = self.client.get_bytes(url).decode("utf-8", errors="replace")
        ts = utc_now_iso()
        p.write_text(body)
        meta.write_text(json.dumps({"url": url, "fetched_utc": ts}))
        return body, ts
