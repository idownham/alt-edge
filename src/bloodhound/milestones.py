"""Kalshi /milestones (category Mentions): Kalshi's own start/end times for mention events.

Candidate start-time source for Vance (Factbase has no Vance calendar), checked against the Factbase
schedule on Trump events first. Read-only, paced <= 1 req/s via KalshiPublic. Raw pages are kept in
data/raw/milestones.json (gitignored). No outcomes are read.
"""
from __future__ import annotations

import json
import sqlite3

from .db import ROOT
from .http import KalshiPublic, utc_now_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS milestones (
    id TEXT PRIMARY KEY,
    event_ticker TEXT,       -- first primary event ticker
    title TEXT,
    type TEXT,
    start_date TEXT,
    end_date TEXT,
    last_updated_ts TEXT,
    fetched_utc TEXT
);
CREATE INDEX IF NOT EXISTS ix_milestones_event ON milestones(event_ticker);
"""
SERIES_PREFIXES = ("KXTRUMPMENTION-", "KXVANCEMENTION-")


def collect_milestones(conn: sqlite3.Connection, api: KalshiPublic, max_pages: int = 400) -> dict:
    conn.executescript(SCHEMA)
    cursor, pages, kept, seen = None, 0, 0, 0
    raw = []
    while pages < max_pages:
        params = {"limit": 500, "category": "mentions"}
        if cursor:
            params["cursor"] = cursor
        body = api.get("/milestones", **params)
        pages += 1
        for m in body.get("milestones", []):
            seen += 1
            evs = m.get("primary_event_tickers") or m.get("related_event_tickers") or []
            ev = next((e for e in evs if e.startswith(SERIES_PREFIXES)), None)
            if ev is None:
                continue
            raw.append(m)
            conn.execute("INSERT OR REPLACE INTO milestones VALUES (?,?,?,?,?,?,?,?)",
                         (m["id"], ev, m.get("title"), m.get("type"), m.get("start_date"), m.get("end_date"),
                          m.get("last_updated_ts"), utc_now_iso()))
            kept += 1
        conn.commit()
        cursor = body.get("cursor")
        if not cursor or not body.get("milestones"):
            break
    out = ROOT / "data" / "raw" / "milestones.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(raw))
    return {"pages": pages, "seen": seen, "kept": kept}
