"""Guards of scripts/score_extension.py (no real outcomes)."""
import importlib.util
import sqlite3

import pytest

from bloodhound import db

spec = importlib.util.spec_from_file_location("score_extension", db.ROOT / "scripts" / "score_extension.py")
ext = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ext)


def test_refuses_before_nov_21(tmp_path):
    (tmp_path / "scored-test.json").write_text("{}")
    with pytest.raises(SystemExit):
        ext.check_run_allowed("2026-11-20", tmp_path)
    ext.check_run_allowed("2026-11-21", tmp_path)


def test_refuses_without_test_or_twice(tmp_path):
    with pytest.raises(SystemExit):
        ext.check_run_allowed("2026-11-25", tmp_path)
    (tmp_path / "scored-test.json").write_text("{}")
    (tmp_path / "scored-locked.json").write_text("{}")
    with pytest.raises(SystemExit):
        ext.check_run_allowed("2026-11-25", tmp_path)


def test_inconclusive_after_extension_is_stop():
    assert ext.final_verdict("INCONCLUSIVE (x)").startswith("STOP")
    assert ext.final_verdict("PASS (calibration gate)").startswith("PASS")
    assert ext.final_verdict("STOP (model Brier >= market Brier)").startswith("STOP")


def test_extension_window():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE events (event_ticker, series, period, first_close)")
    c.executemany("INSERT INTO events VALUES (?,?,?,?)", [
        ("A", "KXTRUMPMENTION", "locked", "2026-11-20T23:00:00Z"),
        ("B", "KXTRUMPMENTION", "locked", "2026-11-21T01:00:00Z"),
        ("C", "KXVANCEMENTION", "locked", "2026-11-01T00:00:00Z"),
        ("D", "KXTRUMPMENTION", "test", "2026-10-01T00:00:00Z")])
    assert ext.extension_events(c) == {"A"}
