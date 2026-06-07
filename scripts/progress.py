"""Versioned, atomic course progress persistence."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


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
        "user_preferences": {
            "learning_style": "unknown",
            "pace": "normal",
            "notes": "",
        },
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
    return errors


def save_progress(course_dir: str | Path, data: dict[str, Any]) -> Path:
    path = progress_path(course_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = dict(data)
    data["schema_version"] = SCHEMA_VERSION
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
    errors = validate_progress(data)
    if errors:
        raise ValueError("; ".join(errors))
    return data
