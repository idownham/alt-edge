"""Collector #1: every settled market of the mention series, with full rules. Outcomes go to the
separate `results` table (read only via db.outcomes)."""
from __future__ import annotations

import datetime as dt
import re
import sqlite3

from .http import KalshiPublic, utc_now_iso
from .split import period_for_first_close

SERIES = ("KXTRUMPMENTION", "KXVANCEMENTION")

_DESC_RE = re.compile(r"say (?:during|at|in|on)\s+(?P<desc>.+?)(?:,?\s+(?:originally )?scheduled for .*)?\?*\s*$")
_TICKER_DATE_RE = re.compile(r"-(?P<yy>\d\d)(?P<mon>[A-Z]{3})(?P<dd>\d\d)(?:[A-Z]|-?\d)?$")
_MONTHS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], start=1)}


def parse_event_desc(title: str) -> str | None:
    """'What will Donald Trump say during X originally scheduled for October 14, 2026?' -> 'X'."""
    m = _DESC_RE.search(title or "")
    return m.group("desc").strip() if m else None


def ticker_date(event_ticker: str) -> str | None:
    """'KXTRUMPMENTION-26OCT14' / '-26MAY01C' -> '2026-10-14' / '2026-05-01' (Kalshi's listed date)."""
    m = _TICKER_DATE_RE.search(event_ticker)
    if not m or m.group("mon") not in _MONTHS:
        return None
    return dt.date(2000 + int(m.group("yy")), _MONTHS[m.group("mon")], int(m.group("dd"))).isoformat()


def _iter_pages(api: KalshiPublic, path: str, **params):
    cursor = None
    while True:
        body = api.get(path, limit=1000, cursor=cursor, **params)
        yield body.get("markets", []), utc_now_iso()
        cursor = body.get("cursor")
        if not cursor:
            break


def collect(conn: sqlite3.Connection, api: KalshiPublic, series=SERIES) -> dict[str, int]:
    counts = {}
    for s in series:
        n = 0
        for path, params in (("/historical/markets", {"series_ticker": s}),
                             ("/markets", {"series_ticker": s, "status": "settled"})):
            for markets, fetched in _iter_pages(api, path, **params):
                for m in markets:
                    if m.get("status") not in ("settled", "finalized") or m.get("result") not in ("yes", "no"):
                        continue
                    word = (m.get("custom_strike") or {}).get("Word") or m.get("yes_sub_title")
                    conn.execute(
                        "INSERT OR REPLACE INTO markets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (m["ticker"], m["event_ticker"], s, word, m.get("title"), m.get("rules_primary"),
                         m.get("rules_secondary"), m.get("open_time"), m.get("close_time"),
                         m.get("occurrence_datetime"), int(bool(m.get("can_close_early"))),
                         m.get("strike_type"), path, fetched))
                    conn.execute("INSERT OR REPLACE INTO results VALUES (?,?,?,?)",
                                 (m["ticker"], m["result"], m.get("settlement_ts"), fetched))
                    n += 1
        counts[s] = n
    rebuild_events(conn)
    conn.commit()
    return counts


def rebuild_events(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM events")
    rows = conn.execute("SELECT event_ticker, series, MIN(close_time) AS first_close, COUNT(*) AS n, "
                        "MIN(title) AS title FROM markets GROUP BY event_ticker").fetchall()
    for r in rows:
        desc, date = parse_event_desc(r["title"]), ticker_date(r["event_ticker"])
        conn.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?)",
                     (r["event_ticker"], r["series"], r["title"], desc, date, r["first_close"],
                      period_for_first_close(r["first_close"]), r["n"]))
