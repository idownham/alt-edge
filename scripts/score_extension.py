"""One-time extension scoring after the INCONCLUSIVE test result (decisions.md, 2026-11-09 pooling rule).

Usage (after 2026-11-21 UTC, once the extension data has been collected and committed):
    python scripts/score_extension.py --frozen-hash bb92f3a

Lives outside src/ so the freeze guard (src/, pyproject.toml, frozen_model.json unchanged) still holds;
uses only the frozen functions. Pooled test + extension -> PASS or STOP.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys

from bloodhound import db
from bloodhound.backtest import (blend_prob, by_type, corpus_fingerprint, gate_verdict, load_frozen, load_markets,
                                 summarize)
from bloodhound.http import utc_now_iso
from bloodhound.model import load_corpus, predict

EXT_LAST_CLOSE = "2026-11-20"
EARLIEST_RUN = "2026-11-21"
RECORDED_TEST = (0.1614, 0.1631)  # docs/results/score-test-2026-11-10.md (4 dp)
RESULTS = db.ROOT / "docs" / "results"


def extension_events(conn, last_close: str = EXT_LAST_CLOSE) -> set[str]:
    rows = conn.execute("SELECT event_ticker FROM events WHERE period='locked' AND series='KXTRUMPMENTION' "
                        "AND substr(first_close,1,10) <= ?", (last_close,)).fetchall()
    return {r[0] for r in rows}


def final_verdict(pooled_verdict: str) -> str:
    """After the extension only PASS or STOP is allowed: a still-inconclusive pooled result is STOP."""
    if pooled_verdict.startswith("PASS"):
        return pooled_verdict
    if pooled_verdict.startswith("INCONCLUSIVE"):
        return "STOP (no demonstrated edge: pooled result still inconclusive after the one extension)"
    return pooled_verdict


def check_run_allowed(today: str, results=RESULTS) -> None:
    if today < EARLIEST_RUN:
        raise SystemExit(f"refusing: the extension runs through {EXT_LAST_CLOSE}; run on/after {EARLIEST_RUN}")
    if not (results / "scored-test.json").exists():
        raise SystemExit("refusing: the test set has not been scored")
    if (results / "scored-locked.json").exists():
        raise SystemExit("refusing: the extension was already scored (it is scored exactly once)")


def records(conn, docs, period, base, w, frozen_hash, keep=None):
    markets = load_markets(conn, period)
    if keep is not None:
        markets = [m for m in markets if m["event_ticker"] in keep]
    out = db.outcomes(conn, period, score_test=True, frozen_hash=frozen_hash)
    recs = []
    for m in markets:
        if m["ticker"] in out:
            pb = predict(docs, m["word"], m["event_date"], m["etype"], base)[0]
            recs.append({**m, "y": 1 if out[m["ticker"]] == "yes" else 0, "p_base": pb,
                         "p_blend": blend_prob(w, float(m["p_mkt"]), pb)})
    return recs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen-hash", required=True)
    a = ap.parse_args(argv)
    check_run_allowed(dt.datetime.now(dt.timezone.utc).date().isoformat())
    conn = db.connect()
    docs = load_corpus(conn)
    base, w, fz = load_frozen()
    if corpus_fingerprint(docs) != fz["corpus"]:
        raise SystemExit("refusing: transcript corpus up to 2026-10-14 differs from the freeze")
    test = records(conn, docs, "test", base, w, a.frozen_hash)
    t = summarize("frozen blend, test (re-derived)", test, "p_blend")
    if (round(t["brier_model"], 4), round(t["brier_market"], 4)) != RECORDED_TEST:
        raise SystemExit(f"refusing: re-derived test Brier {t['brier_model']:.4f}/{t['brier_market']:.4f} "
                         f"!= recorded {RECORDED_TEST}")
    ext = records(conn, docs, "locked", base, w, a.frozen_hash, keep=extension_events(conn))
    e = summarize("frozen blend, extension", ext, "p_blend")
    pooled = summarize("frozen blend, test + extension (pooled)", test + ext, "p_blend")
    pv = gate_verdict(pooled["n_markets"], pooled["n_events"], pooled["brier_model"], pooled["brier_market"],
                      pooled["hi95"])
    res = {"generated_utc": utc_now_iso(), "frozen_hash": a.frozen_hash, "extension_last_close": EXT_LAST_CLOSE,
           "test": t, "extension": e, "pooled": pooled, "pooled_gate": pv, "final_verdict": final_verdict(pv),
           "by_type_pooled": by_type(test + ext, "p_blend"),
           "base_alone_pooled": summarize("base alone, pooled", test + ext, "p_base")}
    (RESULTS / "scored-locked.json").write_text(json.dumps(
        {"frozen_hash": a.frozen_hash, "final_verdict": res["final_verdict"], "n_ext_markets": e["n_markets"],
         "n_ext_events": e["n_events"]}, indent=1))
    out = RESULTS / f"score-extension-{res['generated_utc'][:10]}.json"
    out.write_text(json.dumps(res, indent=1))
    for r in (t, e, pooled, res["base_alone_pooled"]):
        print(f"{r['name']}: {r['n_events']} ev / {r['n_markets']} mkts  Brier {r['brier_model']:.4f} vs "
              f"{r['brier_market']:.4f}  diff {r['diff']:+.4f} [{r['lo95']:+.4f}, {r['hi95']:+.4f}]")
    print("FINAL:", res["final_verdict"], "->", out)


if __name__ == "__main__":
    sys.exit(main())
