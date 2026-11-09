"""Pre-registered dev/test split (docs/spec.md, criteria v2, confirmed 2026-10-14).

An event's period is set by the close time of its FIRST market:
- dev:    2025-04-02 .. 2026-05-31  (build and tune freely)
- test:   2026-06-01 .. 2026-10-14  (scored exactly once, after the freeze and Ian's OK)
- locked: after 2026-10-14          (decision 2026-11-09: locked like test; only for the one
                                     inconclusive extension through 2026-11-20)

Dates are compared in UTC (YYYY-MM-DD of the ISO close_time), which reproduces the S0 counts
(see tests/test_split.py and the M1 journal entry).
"""
from __future__ import annotations

DEV_END = "2026-05-31"
TEST_START = "2026-06-01"
TEST_END = "2026-10-14"

PERIODS = ("dev", "test", "locked")


def period_for_first_close(first_close_iso: str) -> str:
    day = first_close_iso[:10]
    if day <= DEV_END:
        return "dev"
    if day <= TEST_END:
        return "test"
    return "locked"
