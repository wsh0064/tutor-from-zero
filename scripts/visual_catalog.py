"""Build a source-aware catalog of course visuals for multimodal teaching."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz

from image_extractor import (
    IMAGE_EXTENSIONS,
    extract_from_docx,
    extract_from_pdf,
    extract_from_pptx,
)
from ocr import DEFAULT_LANGUAGES, ocr_image


def _stable_id(source: str, locator: str) -> str:
    return "visual-" + hashlib.sha256(f"{source}\0{locator}".encode("utf-8")).hexdigest()[:16]


def _record(
    root: Path,
    source: Path,
    image: Path,
    locator: str,
    *,
    kind: str,
    languages: str,
) -> dict[str, Any]:
    ocr_text = ""
    ocr_confidence = None
    ocr_error = None
    try:
        result = ocr_image(image, languages=languages)
        ocr_text = result["text"]
        ocr_confidence = result["confidence"]
    except Exception as exc:
        ocr_error = str(exc)
    return {
        "id": _stable_id(source.relative_to(root).as_posix(), locator),
        "path": image.relative_to(root).as_posix(),
        "source_path": source.relative_to(root).as_posix(),
        "locator": locator,
        "kind": kind,
        "provenance": "资料原图",
        "copyright": "source-material",
        "ocr_text": ocr_text,
        "ocr_confidence": ocr_confidence,
        "ocr_error": ocr_error,
        "multimodal_description": "",
        "multimodal_review_status": "pending",
        "related_concepts": [],
        "usability": "unreviewed",
    }


def _pdf_snapshots(source: Path, output: Path, dpi: int = 144) -> list[tuple[Path, str]]:
    generated: list[tuple[Path, str]] = []
    document = fitz.open(source)
    try:
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        for page_number, page in enumerate(document, start=1):
            destination = output / f"page-{page_number}-snapshot.png"
            page.get_pixmap(matrix=matrix, alpha=False).save(destination)
            generated.append((destination, f"page:{page_number}:snapshot"))
    finally:
        document.close()
    return generated


def build_visual_catalog(
    course_dir: str | Path,
    sources: list[Path],
    *,
    languages: str = DEFAULT_LANGUAGES,
    include_pdf_snapshots: bool = True,
) -> dict[str, Any]:
    root = Path(course_dir).resolve()
    image_root = root / ".tutor" / "cache" / "images"
    image_root.mkdir(parents=True, exist_ok=True)
    visuals: list[dict[str, Any]] = []

    for source in sources:
        relative = source.relative_to(root)
        source_key = hashlib.sha256(relative.as_posix().encode("utf-8")).hexdigest()[:16]
        output = image_root / source_key
        output.mkdir(parents=True, exist_ok=True)
        extracted: list[tuple[Path, str, str]] = []
        extension = source.suffix.lower()
        if extension == ".pdf":
            embedded = extract_from_pdf(str(source), str(output))
            extracted.extend(
                (Path(path), Path(path).stem, "embedded-image")
                for path in embedded
            )
            if include_pdf_snapshots:
                extracted.extend(
                    (path, locator, "page-snapshot")
                    for path, locator in _pdf_snapshots(source, output)
                )
        elif extension == ".pptx":
            extracted.extend(
                (Path(path), Path(path).stem, "embedded-image")
                for path in extract_from_pptx(str(source), str(output))
            )
        elif extension == ".docx":
            extracted.extend(
                (Path(path), f"embedded:{index}", "embedded-image")
                for index, path in enumerate(
                    extract_from_docx(str(source), str(output)), start=1
                )
            )
        elif extension in IMAGE_EXTENSIONS:
            destination = output / source.name
            shutil.copy2(source, destination)
            extracted.append((destination, "standalone", "standalone-image"))

        for image, locator, kind in extracted:
            visuals.append(
                _record(
                    root,
                    source,
                    image,
                    locator,
                    kind=kind,
                    languages=languages,
                )
            )

    catalog = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "multimodal_policy": {
            "preferred_interpretation": "direct-vision",
            "ocr_role": "text-recovery-and-search",
            "requires_visual_review_for": [
                "spatial-relations",
                "coordinates",
                "arrows",
                "diagram-structure",
            ],
        },
        "visuals": visuals,
    }
    (root / ".tutor" / "visual_catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return catalog
