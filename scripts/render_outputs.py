"""Render course Markdown outputs into a portable offline review site."""

from __future__ import annotations

import html
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_ROOT / "assets" / "templates"
KATEX_DIR = SKILL_ROOT / "assets" / "vendor" / "katex"


def _inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        r'<figure><img src="\2" alt="\1" loading="lazy"/><figcaption>\1</figcaption></figure>',
        escaped,
    )


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
    math_lines: list[str] = []
    in_math = False
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
        if stripped == r"\[" and not in_code:
            flush_paragraph()
            flush_list()
            in_math = True
            math_lines.clear()
            index += 1
            continue
        if stripped == r"\]" and in_math:
            expression = "\n".join(math_lines)
            output.append(
                '<div class="math-block">\\['
                + html.escape(expression)
                + "\\]</div>"
            )
            math_lines.clear()
            in_math = False
            index += 1
            continue
        if in_math:
            math_lines.append(line)
            index += 1
            continue
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
    if in_math:
        output.append(
            '<div class="math-block math-error">\\['
            + html.escape("\n".join(math_lines))
            + "\\]</div>"
        )
    return "\n".join(output)


def _package_images(markdown: str, course_root: Path, output_dir: Path) -> str:
    image_dir = output_dir / "assets" / "visuals"

    def replace(match: re.Match[str]) -> str:
        alt, target = match.group(1), match.group(2)
        if re.match(r"^(?:https?:|data:)", target, flags=re.IGNORECASE):
            return match.group(0)
        source = Path(target)
        candidates = [source] if source.is_absolute() else [
            course_root / source,
            output_dir / source,
        ]
        resolved = next((path.resolve() for path in candidates if path.is_file()), None)
        if resolved is None:
            return match.group(0)
        image_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:12]
        destination = image_dir / f"{digest}-{resolved.name}"
        shutil.copy2(resolved, destination)
        return f"![{alt}](assets/visuals/{destination.name})"

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, markdown)


def _sections(files: Iterable[Path], course_root: Path, output_dir: Path) -> str:
    sections = []
    for path in files:
        markdown = _package_images(
            path.read_text(encoding="utf-8"),
            course_root,
            output_dir,
        )
        sections.append(
            '<section class="document">'
            f'<div class="source-label">{html.escape(path.name)}</div>'
            f"{markdown_to_html(markdown)}"
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
    if not KATEX_DIR.exists():
        raise FileNotFoundError(
            "缺少离线 KaTeX 资源 assets/vendor/katex，请重新安装完整 Skill"
        )
    site_assets = output_dir / "assets" / "katex"
    if site_assets.exists():
        shutil.rmtree(site_assets)
    shutil.copytree(KATEX_DIR, site_assets)
    math_config = """
<link rel="stylesheet" href="assets/katex/katex.min.css"/>
"""
    math_scripts = """
<script defer src="assets/katex/katex.min.js"></script>
<script defer src="assets/katex/contrib/auto-render.min.js"></script>
"""
    math_init = """
<script>
document.addEventListener("DOMContentLoaded", function () {
  renderMathInElement(document.body, {
    delimiters: [
      {left: "\\\\[", right: "\\\\]", display: true},
      {left: "\\\\(", right: "\\\\)", display: false}
    ],
    throwOnError: false,
    strict: "warn"
  });
});
</script>
"""
    title = f"{root.name} - 复习站点"
    body = (
        f'<main class="course-site"><h1>{html.escape(title)}</h1>'
        f"{_sections(markdown_files, root, output_dir)}</main>"
    )
    rendered = (
        shell.replace("__TITLE__", html.escape(title))
        .replace("__MATHJAX_CONFIG__", math_config)
        .replace("__MATHJAX_SCRIPT__", math_scripts)
        .replace("__CSS__", css)
        .replace("__BODY__", body)
        .replace("__EXTRA_JS__", math_init)
    )
    destination = output_dir / "review-site.html"
    destination.write_text(rendered, encoding="utf-8")
    return destination
