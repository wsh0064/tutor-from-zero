"""Scan a course folder and build a source-aware extraction bundle."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from extract_docx import build_text_summary as docx_summary
from extract_docx import extract_docx
from extract_pdf import build_text_summary as pdf_summary
from extract_pdf import extract_pdf
from extract_pptx import build_text_summary as pptx_summary
from extract_pptx import extract_pptx
from image_extractor import IMAGE_EXTENSIONS, extract_image_text
from ocr import DEFAULT_LANGUAGES


SUPPORTED_EXTENSIONS = {".pdf", ".pptx", ".docx"} | IMAGE_EXTENSIONS
IGNORED_DIRECTORIES = {".tutor", "outputs", ".git", "__pycache__"}


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _signal(path: Path) -> tuple[str, int]:
    name = path.name.lower()
    if any(term in name for term in ("真题", "exam", "quiz", "作业", "assignment")):
        return "exam-or-assignment", 4
    if any(term in name for term in ("讲课", "录音", "transcript", "笔记", "notes")):
        return "lecture-record", 3
    if any(term in name for term in ("ppt", "课件", "教材", "syllabus", "textbook")):
        return "course-material", 2
    if any(term in name for term in ("聊天", "群", "chat", "截图", "screenshot")):
        return "informal-context", 1
    return "unclassified", 2


def discover_files(course_dir: str | Path) -> list[Path]:
    root = Path(course_dir).resolve()
    found = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if any(part in IGNORED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        found.append(path)
    return sorted(found, key=lambda item: str(item.relative_to(root)).lower())


def extract_one(path: Path, languages: str) -> tuple[dict[str, Any], str]:
    extension = path.suffix.lower()
    if extension == ".pdf":
        raw = extract_pdf(str(path), ocr_languages=languages)
        return raw, pdf_summary(raw)
    if extension == ".pptx":
        raw = extract_pptx(str(path))
        return raw, pptx_summary(raw)
    if extension == ".docx":
        raw = extract_docx(str(path))
        return raw, docx_summary(raw)
    raw = extract_image_text(str(path), languages=languages)
    return raw, f"# {path.name}\n\n{raw['text']}"


def build_bundle(
    course_dir: str | Path,
    *,
    languages: str = DEFAULT_LANGUAGES,
    continue_on_error: bool = True,
) -> dict[str, Any]:
    root = Path(course_dir).resolve()
    tutor_dir = root / ".tutor"
    cache_dir = tutor_dir / "cache" / "extracted"
    cache_dir.mkdir(parents=True, exist_ok=True)

    records = []
    merged_parts = []
    for path in discover_files(root):
        relative = path.relative_to(root)
        source_type, signal_strength = _signal(path)
        record: dict[str, Any] = {
            "path": relative.as_posix(),
            "extension": path.suffix.lower(),
            "sha256": _hash_file(path),
            "size_bytes": path.stat().st_size,
            "source_type": source_type,
            "signal_strength": signal_strength,
            "status": "ok",
            "error": None,
        }
        try:
            raw, summary = extract_one(path, languages)
            cache_name = hashlib.sha256(str(relative).encode("utf-8")).hexdigest()[:16]
            (cache_dir / f"{cache_name}.json").write_text(
                json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            (cache_dir / f"{cache_name}.md").write_text(summary, encoding="utf-8")
            record["cache_key"] = cache_name
            record["text_characters"] = len(summary)
            merged_parts.append(
                f"\n\n---\n\n<!-- source: {relative.as_posix()} -->\n{summary}"
            )
        except Exception as exc:
            record["status"] = "error"
            record["error"] = str(exc)
            if not continue_on_error:
                raise
        records.append(record)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    manifest = {
        "schema_version": 1,
        "course_dir": str(root),
        "generated_at": generated_at,
        "ocr_languages": languages,
        "file_count": len(records),
        "successful_files": sum(item["status"] == "ok" for item in records),
        "failed_files": sum(item["status"] == "error" for item in records),
        "files": records,
    }
    bundle = {
        "schema_version": 1,
        "generated_at": generated_at,
        "manifest": manifest,
        "merged_text": "".join(merged_parts).strip(),
    }
    tutor_dir.mkdir(exist_ok=True)
    (tutor_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (tutor_dir / "extraction_bundle.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return bundle
