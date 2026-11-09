"""Base-rate model v1 (s1-plan #5).

P(word) = share of the speaker's last N comparable earlier events whose transcript contains the word
(as many times as the market needs), shrunk toward a prior mean m with strength s (a Beta(s*m, s*(1-m))
prior):  p = (hits + s*m) / (n + s).

- Comparable = same event type (keyword rules, event_types.py), or all events, or same type with a
  fallback to all when the same-type pool has < FALLBACK_MIN events; transcripts with fewer than
  `min_seconds` of Trump speech are skipped.
- No look-ahead: only transcripts dated at least `gap_days` before the event's ET date are used
  (gap_days=1 means strictly earlier dates, as the spec says). `history()` asserts this.
- The word and its count threshold come from the market ("Iran (3+ times)"); the rule-aware matcher
  applies the contract's word-form rules.

Probabilities are floats (scores, not money); market prices stay Decimal until scoring.
"""
from __future__ import annotations

import datetime as dt
import re
import sqlite3
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from .event_types import classify
from .matcher import count_matches_indexed, token_index, tokenize
from .transcripts import load, speaker_text

ET = ZoneInfo("America/New_York")
FALLBACK_MIN = 5
_TIMES = re.compile(r"\s*\((\d+)\+ times\)\s*$", re.I)


@dataclass(frozen=True)
class Params:
    pool: str = "same_type"        # same_type | all | same_type_fallback
    last_n: int = 20
    min_seconds: int = 300
    prior_strength: float = 2.0
    prior_mean: float = 0.5
    gap_days: int = 1


@dataclass
class Doc:
    url: str
    date: str          # ET date of the transcript's event
    etype: str
    seconds: int
    tokens: list[str] = field(repr=False)
    index: dict = field(repr=False)


def parse_word(word: str) -> tuple[str, int]:
    """'Iran (3+ times)' -> ('Iran', 3); 'Tariff' -> ('Tariff', 1)."""
    m = _TIMES.search(word)
    if m:
        return word[:m.start()].strip(), int(m.group(1))
    return word.strip(), 1


def et_date(start_utc: str) -> str:
    t = dt.datetime.strptime(start_utc[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
    return t.astimezone(ET).date().isoformat()


def load_corpus(conn: sqlite3.Connection, speaker_name: str = "Donald Trump") -> list[Doc]:
    rows = conn.execute("SELECT url, date, title, trump_seconds, json_path FROM transcripts "
                        "WHERE status='ok' AND n_trump_segments > 0 ORDER BY date, url").fetchall()
    docs = []
    for r in rows:
        toks = tokenize(speaker_text(load(r["json_path"]), speaker_name))
        docs.append(Doc(r["url"], r["date"], classify(r["title"]), r["trump_seconds"] or 0, toks,
                        token_index(toks)))
    return docs


def cutoff_date(event_date: str, gap_days: int) -> str:
    """Latest transcript date allowed for an event on event_date."""
    return (dt.date.fromisoformat(event_date) - dt.timedelta(days=gap_days)).isoformat()


def history(docs: list[Doc], event_date: str, etype: str, p: Params) -> list[Doc]:
    """Comparable earlier transcripts, most recent first, at most last_n."""
    cut = cutoff_date(event_date, p.gap_days)
    base = [d for d in docs if d.date <= cut and d.seconds >= p.min_seconds]
    if p.pool == "all":
        pool = base
    else:
        pool = [d for d in base if d.etype == etype]
        if p.pool == "same_type_fallback" and len(pool) < FALLBACK_MIN:
            pool = base
    pool = sorted(pool, key=lambda d: (d.date, d.url), reverse=True)[:p.last_n]
    assert all(d.date < event_date for d in pool), "look-ahead: transcript not before the event"
    return pool


def shrink(hits: int, n: int, p: Params) -> float:
    return (hits + p.prior_strength * p.prior_mean) / (n + p.prior_strength)


def predict(docs: list[Doc], word: str, event_date: str, etype: str, p: Params) -> tuple[float, int, int]:
    """-> (probability, hits, n)."""
    spec, need = parse_word(word)
    hist = history(docs, event_date, etype, p)
    hits = sum(count_matches_indexed(spec, d.tokens, d.index) >= need for d in hist)
    return shrink(hits, len(hist), p), hits, len(hist)


class HitTable:
    """Precomputed hit/miss of every market against every transcript, so a parameter grid is cheap.
    For each market and (pool, min_seconds) it keeps the recency-ordered prefix sums of hits among
    transcripts allowed by gap_days."""

    def __init__(self, docs: list[Doc], markets: list[dict], gap_days: int, min_seconds_grid, pools,
                 max_n: int = 1000):
        self.gap_days = gap_days
        self.prefix: dict = {}
        cache: dict[tuple[str, int], list[bool]] = {}
        for mk in markets:
            spec, need = parse_word(mk["word"])
            key = (spec, need)
            if key not in cache:
                cache[key] = [count_matches_indexed(spec, d.tokens, d.index) >= need for d in docs]
            hits = cache[key]
            cut = cutoff_date(mk["event_date"], gap_days)
            order = [i for i in range(len(docs) - 1, -1, -1) if docs[i].date <= cut]  # newest first
            for ms in min_seconds_grid:
                eligible = [i for i in order if docs[i].seconds >= ms]
                same = [i for i in eligible if docs[i].etype == mk["etype"]]
                for pool in pools:
                    if pool == "all":
                        seq = eligible
                    elif pool == "same_type":
                        seq = same
                    else:
                        seq = same if len(same) >= FALLBACK_MIN else eligible
                    assert all(docs[i].date < mk["event_date"] for i in seq)
                    ps = [0]
                    for i in seq[:max_n]:
                        ps.append(ps[-1] + hits[i])
                    self.prefix[(mk["ticker"], pool, ms)] = ps

    def prob(self, ticker: str, p: Params) -> float:
        ps = self.prefix[(ticker, p.pool, p.min_seconds)]
        n = min(p.last_n, len(ps) - 1)
        return shrink(ps[n], n, p)
