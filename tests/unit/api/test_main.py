from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.main import prune_expired_session_logs


def _touch(path: Path, timestamp: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("log line", encoding="utf-8")
    os.utime(path, (timestamp.timestamp(), timestamp.timestamp()))


def test_prune_expired_session_logs_removes_old_files_after_retention_window(tmp_path: Path) -> None:
    now = datetime(2026, 4, 13, 12, 0, tzinfo=UTC)
    recent_file = tmp_path / "active" / "session.log"
    stale_file = tmp_path / "archive" / "old.log"
    _touch(recent_file, now - timedelta(days=2))
    _touch(stale_file, now - timedelta(days=4))

    removed = prune_expired_session_logs(tmp_path, retention_days=3, now=now)

    assert removed == 1
    assert recent_file.exists()
    assert not stale_file.exists()


def test_prune_expired_session_logs_with_non_positive_window_noop(tmp_path: Path) -> None:
    now = datetime(2026, 4, 13, 12, 0, tzinfo=UTC)
    retained_file = tmp_path / "still" / "active.log"
    _touch(retained_file, now - timedelta(days=20))

    removed = prune_expired_session_logs(tmp_path, retention_days=0, now=now)

    assert removed == 0
    assert retained_file.exists()
