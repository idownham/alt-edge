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


# Files that make up the frozen model: scoring a locked period needs them byte-identical to the freeze commit.
FROZEN_PATHS = ("src", "pyproject.toml", "docs/results/frozen_model.json")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def frozen_commit_if_unchanged(frozen_hash: str, repo: Path = ROOT) -> str | None:
    """Full hash of the freeze commit if: the work tree is clean, the commit is an ancestor of HEAD, and
    FROZEN_PATHS are identical at HEAD and at the freeze commit. Else None.
    (Docs such as decisions.md may change after the freeze; the model may not.)"""
    if git_head_if_clean(repo) is None:
        return None
    r = _git(repo, "rev-parse", "--verify", "--quiet", f"{frozen_hash}^{{commit}}")
    if r.returncode != 0:
        return None
    full = r.stdout.strip()
    if _git(repo, "merge-base", "--is-ancestor", full, "HEAD").returncode != 0:
        return None
    if _git(repo, "diff", "--quiet", full, "HEAD", "--", *FROZEN_PATHS).returncode != 0:
        return None
    return full


def outcomes(conn: sqlite3.Connection, period: str, *, score_test: bool = False,
             frozen_hash: str | None = None, check_fn=frozen_commit_if_unchanged) -> dict[str, str]:
    """Map ticker -> 'yes'/'no' for one period.

    dev: always allowed. test/locked: only with score_test=True and frozen_hash naming the freeze
    commit recorded in decisions.md, with the model files unchanged since (frozen_commit_if_unchanged).
    """
    if period != "dev":
        if not score_test or not frozen_hash or len(frozen_hash) < 7:
            raise LockedPeriodError(f"{period} outcomes are locked until the model is frozen and Ian "
                                    "approves scoring (use --score-test with the frozen commit hash).")
        full = check_fn(frozen_hash)
        if full is None or not full.startswith(frozen_hash):
            raise LockedPeriodError(f"model files differ from freeze commit {frozen_hash}, the tree is dirty, "
                                    "or the hash is unknown; refusing.")
    rows = conn.execute(
        "SELECT r.ticker, r.result FROM results r JOIN markets m USING(ticker) "
        "JOIN events e USING(event_ticker) WHERE e.period = ?", (period,)).fetchall()
    return {r["ticker"]: r["result"] for r in rows}
