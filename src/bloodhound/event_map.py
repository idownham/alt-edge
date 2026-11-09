"""Map Kalshi events to Factbase *scheduled* start times; T_ref = start - 15 min (spec v2).

Uses only pre-event information: Kalshi's event title and listed date, and Factbase calendar entries
that describe an event (not movements). Factbase's tags are loose: campaign rallies appear only under
"Pool Report" at their scheduled time (e.g. Bullhead City rally 4:00 PM ET while the President landed
at 4:04 PM, 2026-10-14). Movement/logistics entries ("arrives", "departs", "lid", pool call times,
"Executive Time") record actual times or non-events and are never used. Market close times and
outcomes are never used here (a dev-only diagnostic lives in status.py).
Unmatched or ambiguous events get method 'none' (excluded: "no scheduled start time") and are listed
in the CSV for Ian to review; a manual override CSV (data/event_map_manual.csv) wins if present.
"""
from __future__ import annotations

import csv
import datetime as dt
import re
import sqlite3
from pathlib import Path

from .db import ROOT

T_REF_OFFSET = dt.timedelta(minutes=15)
_NOT_EVENT = re.compile(r"\b(arrives?|departs?|en route|lid|pool call time|executive time|"
                        r"lunch with|intelligence briefing|no public events)\b", re.I)
MIN_SCORE = 0.5
MANUAL = ROOT / "data" / "event_map_manual.csv"

_STOP = set("""the a an of and in on at for with to by from his her their its this that is be will
president presidents donald trump trumps j d jd vance vice participates participate delivers deliver
holds hold gives give during originally scheduled th st nd rd part et am pm""".split())
_MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
           "october", "november", "december"]
_TITLE_DAY = re.compile(r"\b(" + "|".join(m.capitalize() for m in _MONTHS) + r") (\d{1,2})(?:st|nd|rd|th)?\b")


def tokens(text: str | None) -> set[str]:
    words = re.findall(r"[a-z0-9]+", (text or "").lower().replace("’", "'").replace("'s", ""))
    out = set()
    for w in words:
        if w in _STOP or w in _MONTHS or w.isdigit():
            continue
        out.add(w[:-1] if len(w) > 4 and w.endswith("s") else w)
    return out


def match_score(kalshi_desc: str, fb_desc: str | None, fb_loc: str | None) -> float:
    k = tokens(kalshi_desc)
    if not k:
        return 0.0
    f = tokens(fb_desc) | tokens(fb_loc)
    return len(k & f) / len(k)


def jaccard(a: str | None, b: str | None) -> float:
    ta, tb = tokens(a), tokens(b)
    return len(ta & tb) / len(ta | tb) if ta | tb else 0.0


def candidate_dates(listed_date: str | None, desc: str | None) -> list[str]:
    dates = []
    if listed_date:
        d = dt.date.fromisoformat(listed_date)
        dates += [d.isoformat(), (d - dt.timedelta(days=1)).isoformat()]
        m = _TITLE_DAY.search(desc or "")
        if m:
            td = dt.date(d.year, _MONTHS.index(m.group(1).lower()) + 1, int(m.group(2)))
            if abs((td - d).days) <= 3 and td.isoformat() not in dates:
                dates.insert(0, td.isoformat())
    return dates


def t_ref(start_utc: str) -> str:
    s = dt.datetime.strptime(start_utc, "%Y-%m-%dT%H:%M:%SZ") - T_REF_OFFSET
    return s.strftime("%Y-%m-%dT%H:%M:%SZ")


def _manual() -> dict[str, dict]:
    if not MANUAL.exists():
        return {}
    with MANUAL.open() as f:
        return {r["event_ticker"]: r for r in csv.DictReader(f)}


def map_events(conn: sqlite3.Connection, csv_path: str | Path) -> dict:
    manual = _manual()
    conn.execute("DELETE FROM event_map")
    speaker_of = {"KXTRUMPMENTION": "trump", "KXVANCEMENTION": "vance"}
    rows_out = []
    stats: dict[str, int] = {}
    for ev in conn.execute("SELECT * FROM events ORDER BY event_ticker").fetchall():
        speaker = speaker_of.get(ev["series"])
        best = None
        second = 0.0
        note = ""
        if ev["event_ticker"] in manual:
            m = manual[ev["event_ticker"]]
            if m.get("start_utc"):
                best = {"id": None, "start_utc": m["start_utc"], "score": None}
            method, note = ("manual" if best else "none"), m.get("note", "")
        else:
            cands = []
            for d in candidate_dates(ev["scheduled_date"], ev["event_desc"]):
                cands += [c for c in conn.execute(
                    "SELECT * FROM schedule WHERE speaker=? AND date=? AND source_tag != 'Pool Call Time'",
                    (speaker, d)).fetchall() if not _NOT_EVENT.search(c["description"] or "")]
            scored = sorted(((match_score(ev["event_desc"], c["description"], c["location"]), c)
                             for c in cands),
                            key=lambda x: (-x[0], -jaccard(ev["event_desc"], x[1]["description"])))
            if scored and scored[0][0] >= MIN_SCORE:
                top = scored[0]
                rivals = [s for s, c in scored[1:] if c["start_utc"] != top[1]["start_utc"]]
                second = rivals[0] if rivals else 0.0
                runner = next((c for sc, c in scored[1:] if c["start_utc"] != top[1]["start_utc"]), None)
                if second >= top[0] and (runner is None or jaccard(ev["event_desc"], runner["description"])
                                         >= jaccard(ev["event_desc"], top[1]["description"])):
                    note = f"ambiguous: tie at {top[0]:.2f}"
                else:
                    best = {"id": top[1]["id"], "start_utc": top[1]["start_utc"], "score": top[0],
                            "fb": top[1]["description"]}
            elif not speaker or speaker == "vance":
                note = "no Vance schedule source yet (M2 search)" if speaker == "vance" else "no speaker"
            else:
                note = f"no scheduled entry >= {MIN_SCORE} (best {scored[0][0]:.2f})" if scored else \
                    "no scheduled entries on candidate dates"
            method = "auto" if best else "none"
        tr = t_ref(best["start_utc"]) if best else None
        conn.execute("INSERT INTO event_map VALUES (?,?,?,?,?,?,?)",
                     (ev["event_ticker"], best and best["id"], best and best["start_utc"], tr, method,
                      best and best["score"], note))
        key = f"{ev['series']}|{ev['period']}|{method}"
        stats[key] = stats.get(key, 0) + 1
        rows_out.append({"event_ticker": ev["event_ticker"], "period": ev["period"],
                         "kalshi_event": ev["event_desc"], "listed_date": ev["scheduled_date"],
                         "factbase_entry": (best or {}).get("fb", ""), "start_utc": best and best["start_utc"],
                         "t_ref_utc": tr, "method": method,
                         "score": f"{best['score']:.2f}" if best and best["score"] is not None else "",
                         "runner_up": f"{second:.2f}" if second else "", "note": note})
    conn.commit()
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    return dict(sorted(stats.items()))
