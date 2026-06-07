"""Dependency and runtime diagnostics."""

from __future__ import annotations

import importlib.util
import json
import sys
from typing import Any

from ocr import DEFAULT_LANGUAGES, check_ocr


PYTHON_MODULES = {
    "pptx": "python-pptx",
    "docx": "python-docx",
    "pdfplumber": "pdfplumber",
    "fitz": "pymupdf",
    "PIL": "Pillow",
    "pytesseract": "pytesseract",
}


def run_doctor(languages: str = DEFAULT_LANGUAGES) -> dict[str, Any]:
    modules = {
        package: bool(importlib.util.find_spec(module))
        for module, package in PYTHON_MODULES.items()
    }
    ocr = check_ocr(languages)
    return {
        "python": {
            "version": sys.version.split()[0],
            "supported": sys.version_info >= (3, 10),
        },
        "python_packages": modules,
        "ocr": ocr,
        "ready": (
            sys.version_info >= (3, 10)
            and all(modules.values())
            and ocr["ready"]
        ),
    }


def format_report(report: dict[str, Any]) -> str:
    lines = [
        f"Python {report['python']['version']}: "
        + ("OK" if report["python"]["supported"] else "需要 3.10+")
    ]
    for package, present in report["python_packages"].items():
        lines.append(f"{package}: {'OK' if present else '缺失'}")
    ocr = report["ocr"]
    lines.append(f"Tesseract: {ocr['executable'] or '缺失'}")
    lines.append(
        "OCR 语言: "
        + ("OK" if not ocr["missing_languages"] else "缺失 " + ", ".join(ocr["missing_languages"]))
    )
    lines.append(f"总体状态: {'可用' if report['ready'] else '需要修复'}")
    return "\n".join(lines)


if __name__ == "__main__":
    report = run_doctor()
    print(format_report(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ready"] else 1)
