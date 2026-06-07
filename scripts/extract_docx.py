"""Extract paragraphs, headings, tables, and embedded images from DOCX files."""

from __future__ import annotations

import os
from typing import Any

from docx import Document


def extract_docx(filepath: str) -> dict[str, Any]:
    document = Document(filepath)
    paragraphs: list[str] = []
    sections: list[dict[str, str]] = []
    current_heading = ""
    current_content: list[str] = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        paragraphs.append(text)
        if paragraph.style and paragraph.style.name.startswith("Heading"):
            if current_heading or current_content:
                sections.append(
                    {"heading": current_heading, "content": "\n".join(current_content)}
                )
            current_heading = text
            current_content = []
        else:
            current_content.append(text)
    if current_heading or current_content:
        sections.append(
            {"heading": current_heading, "content": "\n".join(current_content)}
        )

    tables = [
        [[cell.text.strip() for cell in row.cells] for row in table.rows]
        for table in document.tables
    ]
    return {
        "filename": os.path.basename(filepath),
        "paragraphs": paragraphs,
        "sections": sections,
        "tables": tables,
    }


def build_text_summary(data: dict[str, Any]) -> str:
    lines = [f"# {data['filename']}"]
    for section in data["sections"]:
        if section["heading"]:
            lines.append(f"\n## {section['heading']}")
        if section["content"]:
            lines.append(section["content"])
    for index, table in enumerate(data["tables"], start=1):
        if not table:
            continue
        width = max(len(row) for row in table)
        rows = [row + [""] * (width - len(row)) for row in table]
        lines.append(f"\n### 表格 {index}")
        lines.append("| " + " | ".join(rows[0]) + " |")
        lines.append("| " + " | ".join(["---"] * width) + " |")
        lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(lines)
