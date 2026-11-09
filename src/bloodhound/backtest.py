"""Calibration backtest (s1-plan #6) and dev-only tuning (M2).

`tune_dev` reads DEV outcomes only (db.outcomes refuses test/locked). Dev events are split by date:
the earlier half (dev-A) picks the parameters, the later half (dev-B) checks them, so the dev numbers
are not just in-sample. `score_period` scores a fixed parameter file on one period; for test/locked it
goes through the same outcomes() guard (needs --score-test and the frozen commit hash).
"""
from __future__ import annotations

import itertools
import json
import math
import sqlite3
from dataclasses import asdict
from decimal import Decimal

from . import db
from .event_types import classify
from .model import HitTable, Params, et_date
from .prices import is_word_market
from .scoring import (brier, clustered_bootstrap_brier_diff, log_loss, market_prob, passes_quote_filter,
                      reliability_table)

SERIES = "KXTRUMPMENTION"
GRID = {
    "pool": ("same_type", "all", "same_type_fallback"),
    "last_n": (5, 10, 20, 40, 80),
    "min_seconds": (0, 300, 900),
    "prior_strength": (0.5, 1.0, 2.0, 4.0, 8.0, 16.0),
}
EPS = 0.01  # clip for logits in the blend


def load_markets(conn: sqlite3.Connection, period: str, series: str = SERIES) -> list[dict]:
    """Markets passing the spec-v2 filters (prices and schedules only, never results)."""
    rows = conn.execute(
        "SELECT m.ticker, m.event_ticker, m.word, e.event_desc, em.start_utc, rp.yes_bid, rp.yes_ask "
        "FROM markets m JOIN events e USING(event_ticker) JOIN event_map em USING(event_ticker) "
        "JOIN ref_prices rp ON rp.ticker = m.ticker "
        "WHERE e.period = ? AND m.series = ? AND em.t_ref_utc IS NOT NULL ORDER BY em.start_utc, m.ticker",
        (period, series)).fetchall()
    out = []
    for r in rows:
        if not is_word_market(r["word"]):
            continue
        bid = Decimal(r["yes_bid"]) if r["yes_bid"] else None
        ask = Decimal(r["yes_ask"]) if r["yes_ask"] else None
        if not passes_quote_filter(bid, ask):
            continue
        out.append({"ticker": r["ticker"], "event_ticker": r["event_ticker"], "word": r["word"],
                    "event_desc": r["event_desc"], "etype": classify(r["event_desc"]),
                    "start_utc": r["start_utc"], "event_date": et_date(r["start_utc"]),
                    "p_mkt": market_prob(bid, ask)})
    return out


def _logit(p: float) -> float:
    p = min(max(p, EPS), 1 - EPS)
    return math.log(p / (1 - p))


def fit_logistic(X: list[list[float]], y: list[int], iters: int = 50, ridge: float = 1e-6) -> list[float]:
    """Plain Newton-Raphson logistic regression (stdlib)."""
    k = len(X[0])
    w = [0.0] * k
    for _ in range(iters):
        g = [0.0] * k
        H = [[ridge if i == j else 0.0 for j in range(k)] for i in range(k)]
        for x, t in zip(X, y):
            z = sum(a * b for a, b in zip(w, x))
            p = 1 / (1 + math.exp(-z))
            for i in range(k):
                g[i] += (p - t) * x[i]
                for j in range(k):
                    H[i][j] += p * (1 - p) * x[i] * x[j]
        step = _solve(H, g)
        w = [a - b for a, b in zip(w, step)]
        if max(abs(s) for s in step) < 1e-9:
            break
    return w


def _solve(A: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * bb for a, bb in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def blend_prob(w: list[float], p_mkt: float, p_base: float) -> float:
    z = w[0] + w[1] * _logit(p_mkt) + w[2] * _logit(p_base)
    return 1 / (1 + math.exp(-z))


def summarize(name: str, recs: list[dict], key: str) -> dict:
    ps = [r[key] for r in recs]
    ys = [r["y"] for r in recs]
    pk = [float(r["p_mkt"]) for r in recs]
    bs = clustered_bootstrap_brier_diff([(r["event_ticker"], r[key], r["p_mkt"], r["y"]) for r in recs])
    return {"name": name, "n_markets": len(recs), "n_events": bs.n_events,
            "brier_model": brier(ps, ys), "brier_market": brier(pk, ys), "logloss_model": log_loss(ps, ys),
            "logloss_market": log_loss(pk, ys), "diff": bs.diff, "lo95": bs.lo95, "hi95": bs.hi95,
            "reliability_model": reliability_table(ps, ys), "reliability_market": reliability_table(pk, ys)}


def by_type(recs: list[dict], key: str) -> list[dict]:
    out = []
    for t in sorted({r["etype"] for r in recs}):
        sub = [r for r in recs if r["etype"] == t]
        ys = [r["y"] for r in sub]
        out.append({"etype": t, "n_markets": len(sub), "n_events": len({r["event_ticker"] for r in sub}),
                    "brier_model": brier([r[key] for r in sub], ys),
                    "brier_market": brier([float(r["p_mkt"]) for r in sub], ys)})
    return out


def tune_dev(conn: sqlite3.Connection, docs, gap_days: int = 1) -> dict:
    markets = load_markets(conn, "dev")
    outcomes = db.outcomes(conn, "dev")  # dev only; test/locked raise LockedPeriodError
    markets = [m for m in markets if m["ticker"] in outcomes]
    for m in markets:
        m["y"] = 1 if outcomes[m["ticker"]] == "yes" else 0
    events = sorted({(m["start_utc"], m["event_ticker"]) for m in markets})
    half = {ev for _, ev in events[:len(events) // 2]}
    A = [m for m in markets if m["event_ticker"] in half]
    B = [m for m in markets if m["event_ticker"] not in half]
    table = HitTable(docs, markets, gap_days, GRID["min_seconds"], GRID["pool"], max_n=max(GRID["last_n"]))

    def grid_scores(recs, prior_mean):
        res = []
        for pool, n, ms, s in itertools.product(*GRID.values()):
            p = Params(pool, n, ms, s, prior_mean, gap_days)
            res.append((brier([table.prob(r["ticker"], p) for r in recs], [r["y"] for r in recs]), p))
        res.sort(key=lambda t: t[0])
        return res

    mA = sum(r["y"] for r in A) / len(A)
    gridA = grid_scores(A, mA)
    best = gridA[0][1]
    for r in markets:
        r["p_base"] = table.prob(r["ticker"], best)
    # blend: logistic on logit(p_mkt), logit(p_base), fit on dev-A
    w = fit_logistic([[1.0, _logit(float(r["p_mkt"])), _logit(r["p_base"])] for r in A], [r["y"] for r in A])
    for r in markets:
        r["p_blend"] = blend_prob(w, float(r["p_mkt"]), r["p_base"])
    mDev = sum(r["y"] for r in markets) / len(markets)
    frozen_base = Params(best.pool, best.last_n, best.min_seconds, best.prior_strength, mDev, gap_days)
    return {
        "gap_days": gap_days, "n_dev_markets": len(markets), "n_dev_events": len(events),
        "dev_A": {"events": len(half), "markets": len(A), "first": events[0][0],
                  "last": max(m["start_utc"] for m in A), "yes_rate": mA},
        "dev_B": {"events": len(events) - len(half), "markets": len(B),
                  "first": min(m["start_utc"] for m in B), "last": events[-1][0]},
        "grid_top": [{"brier_A": b, **asdict(p)} for b, p in gridA[:15]],
        "grid_size": len(gridA),
        "best_params_A": asdict(best),
        "blend_weights": w,
        "candidate_base_params": asdict(frozen_base),
        "results": {
            "base_on_A(in-sample)": summarize("base, dev-A", A, "p_base"),
            "base_on_B(out-of-sample)": summarize("base, dev-B", B, "p_base"),
            "blend_on_A(in-sample)": summarize("blend, dev-A", A, "p_blend"),
            "blend_on_B(out-of-sample)": summarize("blend, dev-B", B, "p_blend"),
        },
        "by_type_B_base": by_type(B, "p_base"),
        "by_type_B_blend": by_type(B, "p_blend"),
        "records": [{k: (str(v) if isinstance(v, Decimal) else v) for k, v in r.items()} for r in markets],
    }


def write_report(res: dict, path_md, path_json) -> None:
    def f(x):
        return f"{x:.4f}"
    L = [f"# Dev backtest — base-rate model v1 (generated {res['generated_utc']})", "",
         "Dev period only (events whose first market closed ≤ 2026-05-31). **No test or locked outcomes were read.**",
         f"Corpus: {res['n_docs']} Factbase transcripts with Trump speech. Look-ahead rule: transcript date ≤ "
         f"event ET date − {res['gap_days']} day(s).", "",
         f"Dev after spec-v2 filters: {res['n_dev_events']} events / {res['n_dev_markets']} markets. Split by event "
         f"start: dev-A = first {res['dev_A']['events']} events / {res['dev_A']['markets']} markets "
         f"({res['dev_A']['first'][:10]} → {res['dev_A']['last'][:10]}); dev-B = last {res['dev_B']['events']} events / "
         f"{res['dev_B']['markets']} markets ({res['dev_B']['first'][:10]} → {res['dev_B']['last'][:10]}).",
         "Parameters are chosen on dev-A only; dev-B is the out-of-sample check.", "",
         f"## Grid (dev-A Brier, {res['grid_size']} combinations, top 15)", "",
         "| Brier A | pool | last N | min secs | prior s | prior m |", "|---|---|---|---|---|---|"]
    for g in res["grid_top"]:
        L.append(f"| {f(g['brier_A'])} | {g['pool']} | {g['last_n']} | {g['min_seconds']} | "
                 f"{g['prior_strength']} | {g['prior_mean']:.3f} |")
    w = res["blend_weights"]
    L += ["", f"Blend (logistic, fit on dev-A): z = {w[0]:.3f} + {w[1]:.3f}·logit(p_mkt) + {w[2]:.3f}·logit(p_base)",
          "", "## Results (Brier: lower is better; diff = model − market, 95% event-clustered bootstrap)", "",
          "| Model, sample | events | markets | Brier model | Brier market | diff | 95% CI | log loss model | log loss market |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in res["results"].values():
        L.append(f"| {r['name']} | {r['n_events']} | {r['n_markets']} | {f(r['brier_model'])} | "
                 f"{f(r['brier_market'])} | {r['diff']:+.4f} | [{r['lo95']:+.4f}, {r['hi95']:+.4f}] | "
                 f"{f(r['logloss_model'])} | {f(r['logloss_market'])} |")
    for key, label in (("base_on_B(out-of-sample)", "base, dev-B"), ("blend_on_B(out-of-sample)", "blend, dev-B")):
        r = res["results"][key]
        L += ["", f"### Reliability, {label} (model | market)", "",
              "| bin | n model | mean p | freq | n market | mean p | freq |", "|---|---|---|---|---|---|---|"]
        for a, b in zip(r["reliability_model"], r["reliability_market"]):
            L.append(f"| {a['bin']} | {a['n']} | {a['mean_p']:.3f} | {a['freq']:.3f} | {b['n']} | "
                     f"{b['mean_p']:.3f} | {b['freq']:.3f} |")
    for key, label in (("by_type_B_base", "base"), ("by_type_B_blend", "blend")):
        L += ["", f"### By event type, dev-B, {label}", "", "| type | events | markets | Brier model | Brier market |",
              "|---|---|---|---|---|"]
        for t in res[key]:
            L.append(f"| {t['etype']} | {t['n_events']} | {t['n_markets']} | {f(t['brier_model'])} | "
                     f"{f(t['brier_market'])} |")
    L += ["", f"Candidate base-model parameters (prior mean re-estimated on all dev): "
          f"`{json.dumps(res['candidate_base_params'])}`", ""]
    path_md.parent.mkdir(parents=True, exist_ok=True)
    path_md.write_text("\n".join(L))
    slim = {k: v for k, v in res.items() if k != "records"}
    path_json.write_text(json.dumps(slim, indent=1))
