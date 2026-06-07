from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from progress import (
    choose_mode,
    load_progress,
    new_progress,
    progress_path,
    save_progress,
)


def test_mode_boundaries() -> None:
    today = date(2026, 6, 7)
    assert choose_mode("2026-06-10", today) == "emergency"
    assert choose_mode("2026-06-11", today) == "compressed"
    assert choose_mode("2026-06-14", today) == "compressed"
    assert choose_mode("2026-06-15", today) == "full"
    assert choose_mode(None, today) == "full"


def test_create_and_load_progress(course_dir) -> None:
    progress = load_progress(course_dir, create=True, exam_date=None)
    assert progress["course_name"] == course_dir.name
    assert progress["mode"] == "full"
    assert progress_path(course_dir).exists()
    assert load_progress(course_dir)["schema_version"] == 1


def test_atomic_save_creates_backup(course_dir) -> None:
    progress = new_progress("测试课程")
    save_progress(course_dir, progress)
    progress["last_session"]["summary"] = "完成第一章"
    save_progress(course_dir, progress)
    assert progress_path(course_dir).with_suffix(".json.bak").exists()


def test_corrupt_progress_recovers_backup(course_dir) -> None:
    progress = new_progress("测试课程")
    save_progress(course_dir, progress)
    progress["last_session"]["summary"] = "新状态"
    save_progress(course_dir, progress)
    progress_path(course_dir).write_text("{bad json", encoding="utf-8")
    recovered = load_progress(course_dir)
    assert recovered["course_name"] == "测试课程"


def test_invalid_progress_is_rejected(course_dir) -> None:
    with pytest.raises(ValueError):
        save_progress(course_dir, {"course_name": "坏数据"})
