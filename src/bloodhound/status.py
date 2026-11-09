"""`bloodhound status`: DB counts and the last batch runs. Counts only - never reads outcomes."""
from __future__ import annotations

import sqlite3
from decimal import Decimal

from .prices import is_word_market
from .scoring import passes_quote_filter, two_sided


def universe_counts(conn: sqlite3.Connection) -> list[dict]:
    """Per series x period: events/markets before filters, then after each spec-v2 filter in order:
    word markets only -> scheduled start found -> price row present -> two-sided -> spread <= 10c."""
    rows = conn.execute(
        "SELECT m.ticker, m.series, m.word, m.event_ticker, e.period, em.t_ref_utc, "
        "rp.ticker IS NOT NULL AS has_price, rp.yes_bid, rp.yes_ask "
        "FROM markets m JOIN events e USING(event_ticker) LEFT JOIN event_map em USING(event_ticker) "
        "LEFT JOIN ref_prices rp ON rp.ticker = m.ticker").fetchall()
    out: dict = {}
    for r in rows:
        k = (r["series"], r["period"])
        d = out.setdefault(k, {s: [set(), 0] for s in
                               ("all", "word", "scheduled", "priced", "two_sided", "spread_ok")})
        def add(stage):
            d[stage][0].add(r["event_ticker"])
            d[stage][1] += 1
        add("all")
        if not is_word_market(r["word"]):
            continue
        add("word")
        if not r["t_ref_utc"]:
            continue
        add("scheduled")
        if not r["has_price"]:
            continue
        add("priced")
        bid = Decimal(r["yes_bid"]) if r["yes_bid"] else None
        ask = Decimal(r["yes_ask"]) if r["yes_ask"] else None
        if not two_sided(bid, ask):
            continue
        add("two_sided")
        if passes_quote_filter(bid, ask):
            add("spread_ok")
    res = []
    for (series, period), d in sorted(out.items()):
        res.append({"series": series, "period": period,
                    **{f"{s}": f"{len(v[0])} ev / {v[1]} mkts" for s, v in d.items()}})
    return res


def status(conn: sqlite3.Connection) -> str:
    lines = ["Project Bloodhound status (read-only batches; nothing runs continuously)"]
    for t in ("markets", "events", "schedule", "event_map", "ref_prices"):
        lines.append(f"  {t:<11} {conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>7}")
    lines.append("Universe after spec-v2 filters (counts only; no outcomes read):")
    stages = ("all", "word", "scheduled", "priced", "two_sided", "spread_ok")
    for r in universe_counts(conn):
        lines.append(f"  {r['series']:<15} {r['period']:<6} " + " | ".join(f"{s}: {r[s]}" for s in stages))
    lines.append("Last runs:")
    for r in conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 5").fetchall():
        lines.append(f"  {r['finished_utc']} {r['command']:<17} requests={r['requests']} {r['note'][:80]}")
    return "\n".join(lines)
