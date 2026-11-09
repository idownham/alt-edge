"""Collector #2b: the 1-minute candle ending at or just before T_ref for every market of a mapped event.

Old markets (settled before Kalshi's historical cutoff) need one request each
(/historical/markets/{t}/candlesticks); newer ones use the batch endpoint (/markets/candlesticks,
one request per event). Paced <= 1 req/s via KalshiPublic. Resumable: markets already in ref_prices
are skipped. Prices only; outcomes are never read here.
"""
from __future__ import annotations

import datetime as dt
import sqlite3
from decimal import Decimal

from .http import HTTPStatusError, KalshiPublic, utc_now_iso

WINDOW = dt.timedelta(hours=24)       # look back this far for the last candle before T_ref
BATCH_WINDOW = dt.timedelta(hours=6)  # smaller window for the multi-market endpoint
BATCH_MAX_CANDLES = 10_000            # API: markets x minutes per batch request (HTTP 400 above, 2026-11-09)
BATCH_CHUNK = min(100, BATCH_MAX_CANDLES // int(BATCH_WINDOW.total_seconds() // 60))  # = 27
NOT_A_WORD = "does not qualify"       # "Event does not qualify" strikes are excluded (spec v2)


def _ts(iso: str) -> int:
    return int(dt.datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc).timestamp())


def _iso(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _side(c: dict, side: str) -> Decimal | None:
    d = c.get(side) or {}
    v = d.get("close_dollars", d.get("close"))
    return Decimal(v) if v not in (None, "") else None


def last_candle_at_or_before(candles: list[dict], t_ref_ts: int) -> dict | None:
    """Pick the candle with the largest end_period_ts <= t_ref_ts (candles may be sparse)."""
    best = None
    for c in candles:
        e = c.get("end_period_ts")
        if e is not None and e <= t_ref_ts and (best is None or e > best["end_period_ts"]):
            best = c
    return best


def is_word_market(word: str | None) -> bool:
    return bool(word) and NOT_A_WORD not in word.lower()


def _store(conn, ticker, t_ref, candle, window_start, endpoint):
    conn.execute("INSERT OR REPLACE INTO ref_prices VALUES (?,?,?,?,?,?,?,?)",
                 (ticker, t_ref, candle and _iso(candle["end_period_ts"]),
                  candle and _str(_side(candle, "yes_bid")), candle and _str(_side(candle, "yes_ask")),
                  window_start, endpoint, utc_now_iso()))


def _str(d: Decimal | None) -> str | None:
    return None if d is None else str(d)


def collect_prices(conn: sqlite3.Connection, api: KalshiPublic, series: str | None = None,
                   limit: int | None = None) -> dict:
    cutoff = api.get("/historical/cutoff")["market_settled_ts"]
    q = ("SELECT m.ticker, m.series, m.word, m.close_time, m.event_ticker, em.t_ref_utc, e.period "
         "FROM markets m JOIN event_map em USING(event_ticker) JOIN events e USING(event_ticker) "
         "WHERE em.t_ref_utc IS NOT NULL AND m.ticker NOT IN (SELECT ticker FROM ref_prices)")
    args: list = []
    if series:
        q += " AND m.series = ?"
        args.append(series)
    q += " ORDER BY CASE e.period WHEN 'dev' THEN 0 WHEN 'test' THEN 1 ELSE 2 END, m.event_ticker, m.ticker"
    todo = [r for r in conn.execute(q, args).fetchall() if is_word_market(r["word"])]
    if limit:
        todo = todo[:limit]
    done = {"historical": 0, "batch": 0, "no_candle": 0}
    batch: dict[str, list] = {}
    for i, r in enumerate(todo):
        t_ref = _ts(r["t_ref_utc"])
        if r["close_time"] < cutoff:
            start = t_ref - int(WINDOW.total_seconds())
            try:
                body = api.get(f"/historical/markets/{r['ticker']}/candlesticks", period_interval=1,
                               start_ts=start, end_ts=t_ref)
                candles = body.get("candlesticks", [])
            except HTTPStatusError as e:
                if e.code not in (400, 404):
                    raise
                candles = []
            c = last_candle_at_or_before(candles, t_ref)
            _store(conn, r["ticker"], r["t_ref_utc"], c, _iso(start), "historical")
            done["historical"] += 1
            done["no_candle"] += c is None
            conn.commit()  # short write transactions: the transcript batch shares the DB
            if i % 50 == 0:
                print(f"{i}/{len(todo)} {r['ticker']}", flush=True)
        else:
            batch.setdefault(r["event_ticker"], []).append(r)
    for ev, rows in batch.items():
        t_ref = _ts(rows[0]["t_ref_utc"])
        for k in range(0, len(rows), BATCH_CHUNK):
            chunk = rows[k:k + BATCH_CHUNK]
            start = t_ref - int(BATCH_WINDOW.total_seconds())
            body = api.get("/markets/candlesticks", market_tickers=",".join(x["ticker"] for x in chunk),
                           period_interval=1, start_ts=start, end_ts=t_ref)
            got = {m["market_ticker"]: m.get("candlesticks", []) for m in body.get("markets", [])}
            for x in chunk:
                c = last_candle_at_or_before(got.get(x["ticker"], []), t_ref)
                endpoint, wstart = "batch", start
                if c is None:  # quiet market: retry alone with the full window
                    wstart = t_ref - int(WINDOW.total_seconds())
                    one = api.get(f"/series/{x['series']}/markets/{x['ticker']}/candlesticks",
                                  period_interval=1, start_ts=wstart, end_ts=t_ref)
                    c = last_candle_at_or_before(one.get("candlesticks", []), t_ref)
                    endpoint = "series"
                _store(conn, x["ticker"], x["t_ref_utc"], c, _iso(wstart), endpoint)
                done["batch"] += 1
                done["no_candle"] += c is None
        conn.commit()
    conn.commit()
    return done
