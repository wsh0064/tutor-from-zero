"""Extract native text, tables, and OCR fallback content from PDF files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import fitz
import pdfplumber
from PIL import Image

from ocr import DEFAULT_LANGUAGES, ocr_image


def _meaningful_text(text: str, minimum_characters: int) -> bool:
    compact = "".join(text.split())
    return len(compact) >= minimum_characters


def _render_page(document: fitz.Document, page_index: int, dpi: int) -> Image.Image:
    page = document.load_page(page_index)
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def extract_pdf(
    filepath: str,
    *,
    ocr_languages: str = DEFAULT_LANGUAGES,
    force_ocr: bool = False,
    minimum_native_characters: int = 40,
    dpi: int = 220,
) -> dict[str, Any]:
    """Extract a PDF and OCR pages whose native text layer is insufficient."""
    pages: list[dict[str, Any]] = []
    fitz_document = fitz.open(filepath)
    try:
        with pdfplumber.open(filepath) as pdf:
            for page_index, page in enumerate(pdf.pages):
                native_text = (page.extract_text() or "").strip()
                tables = []
                for table in page.extract_tables() or []:
                    if table:
                        tables.append([[cell or "" for cell in row] for row in table])

                needs_ocr = force_ocr or not _meaningful_text(
                    native_text, minimum_native_characters
                )
                ocr_text = ""
                confidence = None
                ocr_error = None
                if needs_ocr:
                    try:
                        result = ocr_image(
                            _render_page(fitz_document, page_index, dpi),
                            languages=ocr_languages,
                        )
                        ocr_text = result["text"].strip()
                        confidence = result["confidence"]
                    except Exception as exc:
                        ocr_error = str(exc)

                selected_text = ocr_text if ocr_text else native_text
                pages.append(
                    {
                        "number": page_index + 1,
                        "text": selected_text,
                        "native_text": native_text,
                        "ocr_text": ocr_text,
                        "ocr_used": bool(ocr_text),
                        "ocr_attempted": needs_ocr,
                        "ocr_confidence": confidence,
                        "ocr_error": ocr_error,
                        "tables": tables,
                    }
                )
    finally:
        fitz_document.close()

    return {
        "pages": pages,
        "total_pages": len(pages),
        "filename": os.path.basename(filepath),
        "source_path": str(Path(filepath).resolve()),
    }


def build_text_summary(data: dict[str, Any]) -> str:
    """Build a readable page-preserving Markdown summary."""
    lines = [f"# {data['filename']}", f"共 {data['total_pages']} 页"]
    for page in data["pages"]:
        method = "OCR" if page["ocr_used"] else "文本层"
        lines.append(f"\n## 第 {page['number']} 页 [{method}]")
        if page["text"]:
            lines.append(page["text"])
        elif page["ocr_error"]:
            lines.append(f"> 未能提取本页：{page['ocr_error']}")
        for index, table in enumerate(page.get("tables", []), start=1):
            if not table:
                continue
            lines.append(f"\n### 表格 {index}")
            width = max(len(row) for row in table)
            rows = [row + [""] * (width - len(row)) for row in table]
            lines.append("| " + " | ".join(rows[0]) + " |")
            lines.append("| " + " | ".join(["---"] * width) + " |")
            lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(lines)
