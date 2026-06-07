"""Unified command-line entry point for tutor-from-zero."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from doctor import format_report, run_doctor
from extract_materials import build_bundle
from ocr import DEFAULT_LANGUAGES
from progress import load_progress, progress_path, validate_progress
from render_outputs import render_course


def _course_dir(value: str) -> Path:
    path = Path(value).resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"课程目录不存在: {path}")
    return path


def command_doctor(args: argparse.Namespace) -> int:
    report = run_doctor(args.lang)
    print(format_report(report))
    return 0 if report["ready"] else 1


def command_extract(args: argparse.Namespace) -> int:
    progress = load_progress(
        args.course_dir, create=True, exam_date=args.exam_date
    )
    bundle = build_bundle(
        args.course_dir,
        languages=args.lang,
        continue_on_error=not args.fail_fast,
    )
    print(
        f"提取完成: {bundle['manifest']['successful_files']}/"
        f"{bundle['manifest']['file_count']} 个文件"
    )
    print(f"学习模式: {progress['mode']}")
    print(Path(args.course_dir) / ".tutor" / "extraction_bundle.json")
    return 0 if bundle["manifest"]["failed_files"] == 0 else 2


def command_status(args: argparse.Namespace) -> int:
    progress = load_progress(args.course_dir, create=args.create)
    print(json.dumps(progress, ensure_ascii=False, indent=2))
    return 0


def command_render(args: argparse.Namespace) -> int:
    print(render_course(args.course_dir))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    errors = []
    try:
        progress = load_progress(args.course_dir)
        errors.extend(validate_progress(progress))
    except Exception as exc:
        errors.append(f"progress.json: {exc}")
    manifest_path = Path(args.course_dir) / ".tutor" / "manifest.json"
    if not manifest_path.exists():
        errors.append("缺少 .tutor/manifest.json，请先运行 extract")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("failed_files"):
                errors.append(f"有 {manifest['failed_files']} 个材料提取失败")
        except Exception as exc:
            errors.append(f"manifest.json: {exc}")
    if errors:
        print("验证失败:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("课程工作区验证通过")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="从课程材料到交互复习与输出生成的统一工具"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="检查依赖和 OCR 环境")
    doctor_parser.add_argument("--lang", default=DEFAULT_LANGUAGES)
    doctor_parser.set_defaults(handler=command_doctor)

    extract_parser = subparsers.add_parser("extract", help="提取课程材料")
    extract_parser.add_argument("course_dir", type=_course_dir)
    extract_parser.add_argument("--lang", default=DEFAULT_LANGUAGES)
    extract_parser.add_argument("--exam-date", help="考试日期 YYYY-MM-DD")
    extract_parser.add_argument("--fail-fast", action="store_true")
    extract_parser.set_defaults(handler=command_extract)

    status_parser = subparsers.add_parser("status", help="显示学习状态")
    status_parser.add_argument("course_dir", type=_course_dir)
    status_parser.add_argument("--create", action="store_true")
    status_parser.set_defaults(handler=command_status)

    render_parser = subparsers.add_parser("render", help="渲染离线复习 HTML")
    render_parser.add_argument("course_dir", type=_course_dir)
    render_parser.set_defaults(handler=command_render)

    validate_parser = subparsers.add_parser("validate", help="验证课程工作区")
    validate_parser.add_argument("course_dir", type=_course_dir)
    validate_parser.set_defaults(handler=command_validate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
