from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from progress import (
    choose_mode,
    load_progress,
    migrate_progress,
    new_progress,
    progress_path,
    save_progress,
    update_preferences,
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
    assert load_progress(course_dir)["schema_version"] == 2
    assert progress["user_preferences"]["onboarding_status"] == "pending"


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


def test_v1_progress_migrates_without_losing_fields(course_dir) -> None:
    path = progress_path(course_dir)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "course_name": "高等数学",
                "started_at": "2026-06-01",
                "updated_at": "2026-06-01T00:00:00+00:00",
                "exam_date": None,
                "mode": "full",
                "chapters": {},
                "wrong_questions": [],
                "user_preferences": {
                    "learning_style": "example-oriented",
                    "pace": "detailed",
                    "custom_field": "keep-me",
                },
                "custom_top_level": {"keep": True},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    migrated = load_progress(course_dir)
    assert migrated["schema_version"] == 2
    assert migrated["custom_top_level"] == {"keep": True}
    assert migrated["user_preferences"]["custom_field"] == "keep-me"
    assert migrated["user_preferences"]["teaching_entry"] == "example-first"
    assert migrated["user_preferences"]["detail_level"] == "detailed"


def test_preferences_require_explicit_confirmation() -> None:
    progress = new_progress("高等数学")
    changed = update_preferences(progress, teaching_entry="map-first")
    assert changed["user_preferences"]["onboarding_status"] == "pending"
    confirmed = update_preferences(
        changed,
        interaction_cadence="frequent-checks",
        guidance_style="independent-first",
        confirmed=True,
    )
    assert confirmed["user_preferences"]["onboarding_status"] == "complete"
    assert confirmed["user_preferences"]["confirmed_at"]
