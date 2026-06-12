"""Versioned, atomic course progress persistence."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2

DEFAULT_USER_PREFERENCES = {
    "onboarding_status": "pending",
    "teaching_entry": "unknown",
    "interaction_cadence": "balanced",
    "guidance_style": "step-by-step",
    "detail_level": "normal",
    "visual_density": "core-concept",
    "formula_style": "rendered",
    "confirmed_at": None,
    "notes": "",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def progress_path(course_dir: str | Path) -> Path:
    return Path(course_dir).resolve() / ".tutor" / "progress.json"


def choose_mode(exam_date: str | None, today: date | None = None) -> str:
    """Choose full, compressed, or emergency mode from days remaining."""
    if not exam_date:
        return "full"
    current = today or date.today()
    remaining = (date.fromisoformat(exam_date) - current).days
    if remaining <= 3:
        return "emergency"
    if remaining <= 7:
        return "compressed"
    return "full"


def new_progress(
    course_name: str,
    exam_date: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "course_name": course_name,
        "started_at": date.today().isoformat(),
        "updated_at": _now(),
        "exam_date": exam_date,
        "mode": choose_mode(exam_date),
        "material_quality": {
            "overall": "unknown",
            "weak_sections": [],
            "notes": "",
        },
        "chapters": {},
        "wrong_questions": [],
        "user_preferences": dict(DEFAULT_USER_PREFERENCES),
        "last_session": {
            "summary": "",
            "next_action": "",
        },
    }


def validate_progress(data: dict[str, Any]) -> list[str]:
    errors = []
    required = {
        "schema_version",
        "course_name",
        "started_at",
        "updated_at",
        "mode",
        "chapters",
        "wrong_questions",
        "user_preferences",
    }
    missing = sorted(required - data.keys())
    if missing:
        errors.append("缺少字段: " + ", ".join(missing))
    if data.get("mode") not in {"full", "compressed", "emergency"}:
        errors.append("mode 必须是 full、compressed 或 emergency")
    if not isinstance(data.get("chapters"), dict):
        errors.append("chapters 必须是对象")
    if not isinstance(data.get("wrong_questions"), list):
        errors.append("wrong_questions 必须是数组")
    preferences = data.get("user_preferences")
    if not isinstance(preferences, dict):
        errors.append("user_preferences 必须是对象")
    elif preferences.get("onboarding_status") not in {"pending", "complete"}:
        errors.append("user_preferences.onboarding_status 必须是 pending 或 complete")
    return errors


def migrate_progress(data: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Upgrade older progress records without discarding unknown fields."""
    migrated = dict(data)
    changed = migrated.get("schema_version") != SCHEMA_VERSION
    preferences = migrated.get("user_preferences")
    if not isinstance(preferences, dict):
        preferences = {}
        changed = True
    else:
        preferences = dict(preferences)

    legacy_style = preferences.get("learning_style")
    legacy_pace = preferences.get("pace")
    for key, value in DEFAULT_USER_PREFERENCES.items():
        if key not in preferences:
            preferences[key] = value
            changed = True
    if legacy_style and preferences["teaching_entry"] == "unknown":
        mapping = {
            "example-oriented": "example-first",
            "system-oriented": "map-first",
            "analogy-oriented": "intuition-first",
        }
        preferences["teaching_entry"] = mapping.get(legacy_style, "unknown")
        changed = True
    if legacy_pace and preferences["detail_level"] == "normal":
        preferences["detail_level"] = legacy_pace
        changed = True

    migrated["user_preferences"] = preferences
    migrated["schema_version"] = SCHEMA_VERSION
    return migrated, changed


def update_preferences(
    data: dict[str, Any],
    *,
    teaching_entry: str | None = None,
    interaction_cadence: str | None = None,
    guidance_style: str | None = None,
    detail_level: str | None = None,
    visual_density: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Return a progress record with explicit, user-approved preference changes."""
    updated, _ = migrate_progress(data)
    updated = dict(updated)
    preferences = dict(updated["user_preferences"])
    values = {
        "teaching_entry": teaching_entry,
        "interaction_cadence": interaction_cadence,
        "guidance_style": guidance_style,
        "detail_level": detail_level,
        "visual_density": visual_density,
    }
    for key, value in values.items():
        if value is not None:
            preferences[key] = value
    if confirmed:
        preferences["onboarding_status"] = "complete"
        preferences["confirmed_at"] = _now()
    updated["user_preferences"] = preferences
    return updated


def save_progress(course_dir: str | Path, data: dict[str, Any]) -> Path:
    path = progress_path(course_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    data, _ = migrate_progress(data)
    data["updated_at"] = _now()
    data["mode"] = choose_mode(data.get("exam_date"))
    errors = validate_progress(data)
    if errors:
        raise ValueError("; ".join(errors))

    if path.exists():
        shutil.copy2(path, path.with_suffix(".json.bak"))
    handle, temp_name = tempfile.mkstemp(
        prefix="progress-", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return path


def load_progress(
    course_dir: str | Path,
    *,
    create: bool = False,
    exam_date: str | None = None,
) -> dict[str, Any]:
    path = progress_path(course_dir)
    if not path.exists():
        if not create:
            raise FileNotFoundError(path)
        data = new_progress(Path(course_dir).resolve().name, exam_date)
        save_progress(course_dir, data)
        return data
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        backup = path.with_suffix(".json.bak")
        if not backup.exists():
            raise
        data = json.loads(backup.read_text(encoding="utf-8"))
    data, changed = migrate_progress(data)
    errors = validate_progress(data)
    if errors:
        raise ValueError("; ".join(errors))
    if changed:
        save_progress(course_dir, data)
    return data
