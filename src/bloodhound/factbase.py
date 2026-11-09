"""Roll Call Factbase calendar -> scheduled start times (ET). Pages fetched once (<= 1 page / 2 s) and
cached in data/cache/factbase/ (gitignored; Q4: research only, not redistributed, not used for training)."""
from __future__ import annotations

import datetime as dt
import html as htmllib
import re
import sqlite3
from zoneinfo import ZoneInfo

from .db import ROOT
from .http import CachedPages

ET = ZoneInfo("America/New_York")
CACHE = ROOT / "data" / "cache" / "factbase"
_MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
                "october", "november", "december"]

_WEEKDAY = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?$")
_DATE = re.compile(r"^([A-Z][a-z]+ \d{1,2}, \d{4})$")
_TIME = re.compile(r"^(\d{1,2}):(\d{2}) (AM|PM)$")
_SKIP_TEXT = {"Full Text and Analysis", "Video", "Watch", "Transcript"}


def calendar_url(speaker: str, year: int, month: int) -> str:
    return f"https://rollcall.com/factbase/{speaker}/calendar/{_MONTH_NAMES[month - 1]}-{year}/"


def _tokens(page: str):
    page = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S)
    for m in re.finditer(r"(<[^>]+>)|([^<]+)", page):
        tagtxt, text = m.group(1), m.group(2)
        if tagtxt is not None:
            tip = re.search(r'data-tooltip="([^"]*)"', tagtxt)
            href = re.match(r'<a [^>]*href="([^"]+)"', tagtxt)
            if tip:
                yield ("tag", htmllib.unescape(tip.group(1)))
            elif href and "/transcript/" in href.group(1):
                yield ("link", href.group(1))
        else:
            t = re.sub(r"\s+", " ", htmllib.unescape(text)).strip()
            if t:
                yield ("text", t)


def parse_calendar(page: str) -> list[dict]:
    """Return entries {date, time_et, description, location, source_tag, transcript_url}."""
    events: list[dict] = []
    date = None
    pending_weekday = False
    tag = None
    cur = None
    last_time_token = None
    for kind, val in _tokens(page):
        if kind == "tag":
            tag = val
            continue
        if kind == "link":
            if cur is not None and not cur["transcript_url"]:
                cur["transcript_url"] = val
            continue
        if _WEEKDAY.match(val):
            pending_weekday = True
            continue
        if pending_weekday and _DATE.match(val):
            date = dt.datetime.strptime(val, "%B %d, %Y").date().isoformat()
            pending_weekday = False
            cur = None
            continue
        pending_weekday = False
        tm = _TIME.match(val)
        if tm and date:
            hh, mm, ap = int(tm.group(1)), int(tm.group(2)), tm.group(3)
            hh = hh % 12 + (12 if ap == "PM" else 0)
            t24 = f"{hh:02d}:{mm:02d}"
            if cur is not None and last_time_token == t24 and not cur["_texts"]:
                continue  # desktop + mobile copies of the same time
            cur = {"date": date, "time_et": t24, "source_tag": tag, "transcript_url": None, "_texts": []}
            events.append(cur)
            last_time_token = t24
            continue
        if cur is not None and val not in _SKIP_TEXT:
            cur["_texts"].append(val)
    out = []
    for e in events:
        texts = e.pop("_texts")
        e["description"] = texts[0] if texts else None
        e["location"] = texts[1] if len(texts) > 1 else None
        out.append(e)
    return out


def start_utc(date: str, time_et: str) -> str:
    local = dt.datetime.fromisoformat(f"{date}T{time_et}").replace(tzinfo=ET)
    return local.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _months(start: str, end: str):
    y, m = map(int, start.split("-"))
    ye, me = map(int, end.split("-"))
    while (y, m) <= (ye, me):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def collect_schedule(conn: sqlite3.Connection, speaker: str, start: str, end: str,
                     refresh_last: bool = False, pages: CachedPages | None = None) -> tuple[int, int]:
    pages = pages or CachedPages(CACHE)
    months = list(_months(start, end))
    n = 0
    for i, (y, m) in enumerate(months):
        url = calendar_url(speaker, y, m)
        page, fetched = pages.get(url, refresh=refresh_last and i == len(months) - 1)
        for e in parse_calendar(page):
            conn.execute(
                "INSERT OR REPLACE INTO schedule(speaker, date, time_et, start_utc, description, location, "
                "source_tag, transcript_url, calendar_url, fetched_utc) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (speaker, e["date"], e["time_et"], start_utc(e["date"], e["time_et"]), e["description"],
                 e["location"], e["source_tag"], e["transcript_url"], url, fetched))
            n += 1
    conn.commit()
    return n, pages.client.requests_made
