"""SQLite store. Outcomes live in their own table and are read only through `outcomes()`,
which refuses test/locked periods unless the frozen-model check passes (spec: test scored once)."""
from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "bloodhound.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS markets (
    ticker TEXT PRIMARY KEY,
    event_ticker TEXT NOT NULL,
    series TEXT NOT NULL,
    word TEXT,
    title TEXT,
    rules_primary TEXT,
    rules_secondary TEXT,
    open_time TEXT,
    close_time TEXT,
    occurrence_datetime TEXT,
    can_close_early INTEGER,
    strike_type TEXT,
    source_endpoint TEXT,
    fetched_utc TEXT
);
CREATE INDEX IF NOT EXISTS ix_markets_event ON markets(event_ticker);

-- Outcomes: never SELECT directly in analysis code; use db.outcomes().
CREATE TABLE IF NOT EXISTS results (
    ticker TEXT PRIMARY KEY REFERENCES markets(ticker),
    result TEXT,
    settlement_ts TEXT,
    fetched_utc TEXT
);

CREATE TABLE IF NOT EXISTS events (
    event_ticker TEXT PRIMARY KEY,
    series TEXT NOT NULL,
    title TEXT,
    event_desc TEXT,
    scheduled_date TEXT,
    first_close TEXT,
    period TEXT NOT NULL,
    n_markets INTEGER
);

CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    speaker TEXT NOT NULL,
    date TEXT NOT NULL,          -- YYYY-MM-DD (ET)
    time_et TEXT,                -- HH:MM 24h, ET
    start_utc TEXT,              -- ISO UTC
    description TEXT,
    location TEXT,
    source_tag TEXT,             -- e.g. "Official Schedule", "Pool Report"
    transcript_url TEXT,
    calendar_url TEXT,
    fetched_utc TEXT,
    UNIQUE(speaker, date, time_et, description)
);

CREATE TABLE IF NOT EXISTS event_map (
    event_ticker TEXT PRIMARY KEY,
    schedule_id INTEGER REFERENCES schedule(id),
    start_utc TEXT,
    t_ref_utc TEXT,
    method TEXT,                 -- auto | manual | none
    score REAL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS ref_prices (
    ticker TEXT PRIMARY KEY,
    t_ref_utc TEXT NOT NULL,
    candle_end_utc TEXT,         -- NULL = no candle at or before T_ref in the window
    yes_bid TEXT,                -- Decimal dollars as text
    yes_ask TEXT,
    window_start_utc TEXT,
    endpoint TEXT,
    fetched_utc TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT,
    started_utc TEXT,
    finished_utc TEXT,
    requests INTEGER,
    note TEXT
);
"""


def connect(path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=60)  # two paced batches (Kalshi, Factbase) may write at once
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


class LockedPeriodError(PermissionError):
    pass


def git_head_if_clean(repo: Path = ROOT) -> str | None:
    """Return HEAD hash if the work tree has no uncommitted changes to tracked files, else None."""
    try:
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=repo,
                               capture_output=True, text=True, check=True).stdout.strip()
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return None if dirty else head


def outcomes(conn: sqlite3.Connection, period: str, *, score_test: bool = False,
             frozen_hash: str | None = None, head_fn=git_head_if_clean) -> dict[str, str]:
    """Map ticker -> 'yes'/'no' for one period.

    dev: always allowed. test/locked: only with score_test=True and frozen_hash equal to the
    current clean git HEAD (the hash recorded in decisions.md at the freeze).
    """
    if period != "dev":
        if not score_test or not frozen_hash:
            raise LockedPeriodError(f"{period} outcomes are locked until the model is frozen and Ian "
                                    "approves scoring (use --score-test with the frozen commit hash).")
        head = head_fn()
        if head is None or not head.startswith(frozen_hash):
            raise LockedPeriodError(f"frozen hash {frozen_hash} != clean HEAD {head}; refusing.")
    rows = conn.execute(
        "SELECT r.ticker, r.result FROM results r JOIN markets m USING(ticker) "
        "JOIN events e USING(event_ticker) WHERE e.period = ?", (period,)).fetchall()
    return {r["ticker"]: r["result"] for r in rows}
