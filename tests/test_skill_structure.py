from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_required_structure_exists() -> None:
    required = [
        "SKILL.md",
        "LICENSE",
        "THIRD_PARTY_NOTICES.md",
        "requirements.txt",
        "scripts/tutor.py",
        "scripts/doctor.py",
        "scripts/extract_materials.py",
        "scripts/ocr.py",
        "scripts/progress.py",
        "scripts/render_outputs.py",
        "assets/templates/page_template.html",
        "references/teaching-workflow.md",
        "references/pedagogy-and-adaptation.md",
        "references/practice-and-exams.md",
        "references/materials-and-confidence.md",
        "references/progress-schema.md",
        "references/subject-strategies.md",
        "references/visual-and-formula-style.md",
        "assets/vendor/katex/katex.min.css",
        "assets/vendor/katex/katex.min.js",
        "assets/vendor/katex/contrib/auto-render.min.js",
    ]
    missing = [item for item in required if not (ROOT / item).exists()]
    assert not missing


def test_skill_frontmatter_and_name() -> None:
    content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert content.startswith("---\n")
    frontmatter = content.split("---", 2)[1]
    assert re.search(r"^name: tutor-from-zero$", frontmatter, re.MULTILINE)
    assert re.search(r"^description: .+", frontmatter, re.MULTILINE)
    assert re.search(r"^license: .+", frontmatter, re.MULTILINE)
    assert len(content.splitlines()) < 500


def test_skill_references_resolve() -> None:
    content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)]+)\)", content)
    missing = [link for link in links if not (ROOT / link).exists()]
    assert not missing


def test_no_platform_specific_configuration() -> None:
    forbidden = [
        ROOT / "agents" / "openai.yaml",
        ROOT / ".cursor",
        ROOT / ".claude",
        ROOT / ".trae",
    ]
    assert not any(path.exists() for path in forbidden)
