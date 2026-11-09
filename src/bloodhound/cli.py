"""`bloodhound` command. Every network command is a one-off, hand-run, paced batch (no services)."""
from __future__ import annotations

import argparse
import json
import sys

from . import db
from .http import KalshiPublic, utc_now_iso


def _log_run(conn, command, started, requests, note=""):
    conn.execute("INSERT INTO runs(command, started_utc, finished_utc, requests, note) VALUES (?,?,?,?,?)",
                 (command, started, utc_now_iso(), requests, note))
    conn.commit()


def cmd_collect_markets(args):
    from .collect_markets import collect
    conn = db.connect(args.db)
    api = KalshiPublic()
    started = utc_now_iso()
    counts = collect(conn, api)
    _log_run(conn, "collect-markets", started, api.client.requests_made, json.dumps(counts))
    print(json.dumps(counts))


def cmd_collect_schedule(args):
    from .factbase import collect_schedule
    conn = db.connect(args.db)
    started = utc_now_iso()
    n, reqs = collect_schedule(conn, args.speaker, args.start, args.end, refresh_last=args.refresh_last)
    _log_run(conn, "collect-schedule", started, reqs, f"{args.speaker} {args.start}..{args.end}: {n} entries")
    print(f"{n} schedule entries; {reqs} page requests")


def cmd_map_events(args):
    from .event_map import map_events
    conn = db.connect(args.db)
    print(json.dumps(map_events(conn, args.csv), indent=1))


def cmd_collect_prices(args):
    from .prices import collect_prices
    conn = db.connect(args.db)
    api = KalshiPublic()
    started = utc_now_iso()
    done = collect_prices(conn, api, series=args.series, limit=args.limit)
    _log_run(conn, "collect-prices", started, api.client.requests_made, json.dumps(done))
    print(json.dumps(done))


def cmd_collect_transcripts(args):
    from .transcripts import collect_transcripts
    conn = db.connect(args.db)
    started = utc_now_iso()
    stats = collect_transcripts(conn, args.speaker, args.since, args.limit)
    _log_run(conn, "collect-transcripts", started, sum(stats.values()), json.dumps(stats))
    print(json.dumps(stats))


def cmd_status(args):
    from .status import status
    print(status(db.connect(args.db)))


def main(argv=None):
    p = argparse.ArgumentParser(prog="bloodhound")
    p.add_argument("--db", default=str(db.DEFAULT_DB))
    sub = p.add_subparsers(required=True)
    sub.add_parser("collect-markets").set_defaults(fn=cmd_collect_markets)
    s = sub.add_parser("collect-schedule")
    s.add_argument("--speaker", default="trump")
    s.add_argument("--start", default="2025-03")
    s.add_argument("--end", default="2026-11")
    s.add_argument("--refresh-last", action="store_true", help="re-fetch the newest month (still changing)")
    s.set_defaults(fn=cmd_collect_schedule)
    m = sub.add_parser("map-events")
    m.add_argument("--csv", default=str(db.ROOT / "data" / "event_map.csv"))
    m.set_defaults(fn=cmd_map_events)
    c = sub.add_parser("collect-prices")
    c.add_argument("--series", default=None)
    c.add_argument("--limit", type=int, default=None, help="max markets this run (resumable)")
    c.set_defaults(fn=cmd_collect_prices)
    t = sub.add_parser("collect-transcripts")
    t.add_argument("--speaker", default="trump")
    t.add_argument("--since", default="2024-01-01")
    t.add_argument("--limit", type=int, default=None)
    t.set_defaults(fn=cmd_collect_transcripts)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
