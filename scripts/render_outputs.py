"""Render course Markdown outputs into a portable offline review site."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_ROOT / "assets" / "templates"


def _inline(text: str) -> str:
    import re

    escaped = html.escape(text)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def _table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def markdown_to_html(markdown: str) -> str:
    """Convert the practical Markdown subset used by study outputs."""
    lines = markdown.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    code_lines: list[str] = []
    in_code = False
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            output.append("<p>" + "<br>".join(_inline(line) for line in paragraph) + "</p>")
            paragraph.clear()

    def flush_list() -> None:
        if list_items:
            output.append("<ul>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ul>")
            list_items.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code:
                output.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        if not stripped:
            flush_paragraph()
            flush_list()
            index += 1
            continue
        if (
            "|" in stripped
            and index + 1 < len(lines)
            and set(lines[index + 1].replace("|", "").replace(":", "").replace("-", "").strip())
            == set()
            and "-" in lines[index + 1]
        ):
            flush_paragraph()
            flush_list()
            headers = _table_cells(stripped)
            index += 2
            rows = []
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                rows.append(_table_cells(lines[index]))
                index += 1
            width = len(headers)
            output.append(
                "<table><thead><tr>"
                + "".join(f"<th>{_inline(cell)}</th>" for cell in headers)
                + "</tr></thead><tbody>"
                + "".join(
                    "<tr>"
                    + "".join(
                        f"<td>{_inline((row + [''] * width)[column])}</td>"
                        for column in range(width)
                    )
                    + "</tr>"
                    for row in rows
                )
                + "</tbody></table>"
            )
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            flush_list()
            output.append(f"<h3>{_inline(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            flush_paragraph()
            flush_list()
            output.append(f"<h2>{_inline(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            flush_paragraph()
            flush_list()
            output.append(f"<h1>{_inline(stripped[2:])}</h1>")
        elif stripped.startswith(("> ", ">\t")):
            flush_paragraph()
            flush_list()
            output.append(f"<blockquote>{_inline(stripped[2:])}</blockquote>")
        elif stripped.startswith(("- ", "* ")):
            flush_paragraph()
            list_items.append(_inline(stripped[2:]))
        else:
            flush_list()
            paragraph.append(line)
        index += 1

    flush_paragraph()
    flush_list()
    if in_code:
        output.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(output)


def _sections(files: Iterable[Path]) -> str:
    sections = []
    for path in files:
        sections.append(
            '<section class="document">'
            f'<div class="source-label">{html.escape(path.name)}</div>'
            f"{markdown_to_html(path.read_text(encoding='utf-8'))}"
            "</section>"
        )
    return "\n".join(sections)


def render_course(course_dir: str | Path) -> Path:
    root = Path(course_dir).resolve()
    output_dir = root / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_files = sorted(output_dir.glob("*.md"))
    if not markdown_files:
        bundle_path = root / ".tutor" / "extraction_bundle.json"
        if not bundle_path.exists():
            raise FileNotFoundError("没有 outputs/*.md 或 .tutor/extraction_bundle.json")
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        fallback = output_dir / "review-guide.md"
        fallback.write_text(
            "# 课程资料提取预览\n\n"
            "> 这是自动提取结果。请由智能体依据 SKILL.md 生成正式复习讲义。\n\n"
            + bundle.get("merged_text", ""),
            encoding="utf-8",
        )
        markdown_files = [fallback]

    shell = (TEMPLATE_DIR / "page_template.html").read_text(encoding="utf-8")
    css = (TEMPLATE_DIR / "base.css").read_text(encoding="utf-8")
    title = f"{root.name} - 复习站点"
    body = f'<main class="course-site"><h1>{html.escape(title)}</h1>{_sections(markdown_files)}</main>'
    rendered = (
        shell.replace("__TITLE__", html.escape(title))
        .replace("__MATHJAX_CONFIG__", "")
        .replace("__MATHJAX_SCRIPT__", "")
        .replace("__CSS__", css)
        .replace("__BODY__", body)
        .replace("__EXTRA_JS__", "")
    )
    destination = output_dir / "review-site.html"
    destination.write_text(rendered, encoding="utf-8")
    return destination
