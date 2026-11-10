"""Freeze guards: model files must match the freeze commit; a locked period is scored once; gate verdicts."""
import subprocess

import pytest

from bloodhound import db
from bloodhound.backtest import gate_verdict


def git(repo, *a):
    return subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "m.py").write_text("x = 1\n")
    (tmp_path / "decisions.md").write_text("a\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "freeze")
    return tmp_path, git(tmp_path, "rev-parse", "HEAD")


def test_docs_may_change_after_freeze(repo):
    path, h = repo
    (path / "decisions.md").write_text("a\nfreeze hash recorded\n")
    git(path, "commit", "-qam", "record hash")
    assert db.frozen_commit_if_unchanged(h[:10], path) == h


def test_model_change_after_freeze_refused(repo):
    path, h = repo
    (path / "src" / "m.py").write_text("x = 2\n")
    assert db.frozen_commit_if_unchanged(h[:10], path) is None   # dirty tree
    git(path, "commit", "-qam", "tweak model")
    assert db.frozen_commit_if_unchanged(h[:10], path) is None   # committed change


def test_unknown_hash_refused(repo):
    path, _ = repo
    assert db.frozen_commit_if_unchanged("deadbeef00", path) is None


def test_short_hash_refused():
    with pytest.raises(db.LockedPeriodError):
        db.outcomes(None, "test", score_test=True, frozen_hash="abc", check_fn=lambda h: "abc123456")


@pytest.mark.parametrize("args,verdict", [
    ((299, 40, 0.15, 0.16, -0.01), "STOP"),
    ((400, 29, 0.15, 0.16, -0.01), "STOP"),
    ((400, 40, 0.17, 0.16, 0.02), "STOP"),
    ((400, 40, 0.16, 0.16, 0.01), "STOP"),
    ((400, 40, 0.15, 0.16, 0.001), "INCONCLUSIVE"),
    ((400, 40, 0.15, 0.16, -0.001), "PASS"),
])
def test_gate_verdict(args, verdict):
    assert gate_verdict(*args).startswith(verdict)
