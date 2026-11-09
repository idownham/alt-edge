"""Collector #3: Factbase transcripts linked from the calendar. <= 1 page / 2 s, each fetched once.
Pages are ~5 MB of HTML, so only the extracted segments are cached (data/cache/transcripts/*.json,
gitignored). Research use only (Q4): not redistributed, not used to train models."""
from __future__ import annotations

import hashlib
import html as htmllib
import json
import re
import sqlite3

from .db import ROOT
from .http import HTTPStatusError, PacedClient, utc_now_iso

CACHE = ROOT / "data" / "cache" / "transcripts"
_SEG = re.compile(
    r'<h2 class="text-md inline">(?P<spk>[^<]*)</h2>\s*<span[^>]*>\s*(?P<t0>\d{2}:\d{2}:\d{2})-(?P<t1>\d{2}:\d{2}:\d{2})'
    r'.*?<div class="\s*flex-auto text-md text-gray-600 leading-loose">(?P<text>.*?)</div>', re.S)
_TITLE = re.compile(r'<meta name="twitter:title" content="([^"]*)"')

SCHEMA = """
CREATE TABLE IF NOT EXISTS transcripts (
    url TEXT PRIMARY KEY,
    date TEXT,             -- calendar date (ET) of the linked schedule entry
    start_utc TEXT,
    title TEXT,
    n_segments INTEGER,
    n_trump_segments INTEGER,
    trump_seconds INTEGER,
    json_path TEXT,
    status TEXT,           -- ok | http_404 | no_segments
    fetched_utc TEXT
);
"""


def _secs(hms: str) -> int:
    h, m, s = map(int, hms.split(":"))
    return h * 3600 + m * 60 + s


def parse_transcript(page: str) -> dict:
    segs = []
    for m in _SEG.finditer(page):
        text = re.sub(r"<[^>]+>", " ", m.group("text"))
        text = re.sub(r"\s+", " ", htmllib.unescape(text)).strip()
        segs.append([htmllib.unescape(m.group("spk")).strip(), m.group("t0"), m.group("t1"), text])
    t = _TITLE.search(page)
    return {"title": htmllib.unescape(t.group(1)) if t else None, "segments": segs}


def speaker_text(doc: dict, speaker: str = "Donald Trump") -> str:
    return " ".join(s[3] for s in doc["segments"] if s[0] == speaker)


def load(json_path: str) -> dict:
    return json.loads((ROOT / json_path).read_text())


def collect_transcripts(conn: sqlite3.Connection, speaker: str = "trump", since: str = "2024-01-01",
                        limit: int | None = None, client: PacedClient | None = None) -> dict:
    conn.executescript(SCHEMA)
    CACHE.mkdir(parents=True, exist_ok=True)
    client = client or PacedClient(min_interval_s=2.0)
    rows = conn.execute(
        "SELECT transcript_url AS url, MIN(date) AS date, MIN(start_utc) AS start_utc FROM schedule "
        "WHERE speaker=? AND transcript_url IS NOT NULL AND date >= ? "
        "AND transcript_url NOT IN (SELECT url FROM transcripts) GROUP BY transcript_url ORDER BY date",
        (speaker, since)).fetchall()
    if limit:
        rows = rows[:limit]
    stats = {"ok": 0, "http_404": 0, "no_segments": 0}
    for i, r in enumerate(rows):
        rel = f"data/cache/transcripts/{hashlib.sha1(r['url'].encode()).hexdigest()[:16]}.json"
        try:
            page = client.get_bytes(r["url"]).decode("utf-8", errors="replace")
        except HTTPStatusError as e:
            if e.code != 404:
                raise
            conn.execute("INSERT OR REPLACE INTO transcripts VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (r["url"], r["date"], r["start_utc"], None, 0, 0, 0, None, "http_404", utc_now_iso()))
            stats["http_404"] += 1
            continue
        doc = parse_transcript(page)
        doc.update(url=r["url"], date=r["date"], fetched_utc=utc_now_iso())
        status = "ok" if doc["segments"] else "no_segments"
        (ROOT / rel).write_text(json.dumps(doc))
        trump = [s for s in doc["segments"] if s[0] == "Donald Trump"]
        conn.execute("INSERT OR REPLACE INTO transcripts VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (r["url"], r["date"], r["start_utc"], doc["title"], len(doc["segments"]), len(trump),
                      sum(max(0, _secs(s[2]) - _secs(s[1])) for s in trump), rel, status, doc["fetched_utc"]))
        stats[status] += 1
        conn.commit()
        if i % 25 == 0:
            print(f"{i}/{len(rows)} {r['date']} {status}", flush=True)
    conn.commit()
    return stats
