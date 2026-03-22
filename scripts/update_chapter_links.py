#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


START_MARKER = "<!-- chapter-links:start -->"
END_MARKER = "<!-- chapter-links:end -->"
CHAPTER_NUMBER_RE = re.compile(r"^(\d+)-")
TOP_NAV_LINE_RE = re.compile(
    r"^(?:<!-- chapter-nav-top:start -->)?\[\u2190 上一章：.+\]\(.+\)(?:<!-- chapter-nav-top:end -->)?$"
)
BOTTOM_NAV_LINE_RE = re.compile(
    r"^(?:<!-- chapter-nav-bottom:start -->)?\[下一章：.+\]\(.+\)(?:<!-- chapter-nav-bottom:end -->)?$"
)


def get_chapter_files(chapters_dir: Path) -> list[Path]:
    return sorted(
        (path for path in chapters_dir.iterdir() if path.is_file() and path.suffix == ".md"),
        key=chapter_sort_key,
    )


def chapter_sort_key(path: Path) -> tuple[int, int, str]:
    match = CHAPTER_NUMBER_RE.match(path.stem)
    if match:
        return (0, int(match.group(1)), path.stem)
    return (1, 0, path.stem)


def markdown_relative_path(source_dir: Path, destination: Path) -> str:
    relative_path = Path(os.path.relpath(destination, source_dir)).as_posix()
    if relative_path.startswith("."):
        return relative_path
    return f"./{relative_path}"


def generate_links(chapter_files: list[Path], base_dir: Path) -> str:
    lines = []
    for path in chapter_files:
        relative_path = markdown_relative_path(base_dir, path)
        title = path.stem
        lines.append(f"- [{title}]({relative_path})")
    return "\n".join(lines)


def replace_between_markers(content: str, generated_links: str) -> str:
    if START_MARKER not in content or END_MARKER not in content:
        raise ValueError(
            f"Missing markers. Add {START_MARKER} and {END_MARKER} to the target markdown file."
        )

    start_index = content.index(START_MARKER) + len(START_MARKER)
    end_index = content.index(END_MARKER)
    replacement = f"\n{generated_links}\n"
    return content[:start_index] + replacement + content[end_index:]


def build_nav_line(linked_path: Path | None, base_dir: Path, label: str) -> str | None:
    if linked_path is None:
        return None

    relative_path = markdown_relative_path(base_dir, linked_path)
    title = linked_path.stem
    return f"[{label}{title}]({relative_path})"


def strip_chapter_nav_lines(content: str) -> str:
    lines = content.splitlines()

    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and TOP_NAV_LINE_RE.fullmatch(lines[0]):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)

    while lines and not lines[-1].strip():
        lines.pop()
    if lines and BOTTOM_NAV_LINE_RE.fullmatch(lines[-1]):
        lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()

    return "\n".join(lines)


def update_chapter_navigation(
    chapter_path: Path,
    previous_path: Path | None,
    next_path: Path | None,
    base_dir: Path,
) -> None:
    content = chapter_path.read_text(encoding="utf-8")
    content = strip_chapter_nav_lines(content)
    content = content.strip("\n")

    top_nav = build_nav_line(
        previous_path,
        base_dir,
        "← 上一章：",
    )
    bottom_nav = build_nav_line(
        next_path,
        base_dir,
        "下一章：",
    )

    if top_nav:
        content = f"{top_nav}\n\n{content}"
    if bottom_nav:
        content = f"{content}\n\n{bottom_nav}"

    chapter_path.write_text(f"{content}\n", encoding="utf-8")


def update_all_chapter_navigation(chapter_files: list[Path], base_dir: Path) -> None:
    for index, chapter_path in enumerate(chapter_files):
        previous_path = chapter_files[index - 1] if index > 0 else None
        next_path = chapter_files[index + 1] if index + 1 < len(chapter_files) else None
        update_chapter_navigation(chapter_path, previous_path, next_path, base_dir)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate markdown links for chapter files and update a markdown file."
    )
    parser.add_argument(
        "--chapters-dir",
        default="manuscript/chapters",
        help="Directory containing chapter markdown files.",
    )
    parser.add_argument(
        "--target",
        default="README.md",
        help="Markdown file to update. Use '-' to print the generated list.",
    )
    parser.add_argument(
        "--update-chapter-navs",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Update previous/next navigation links inside chapter markdown files.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    chapters_dir = (repo_root / args.chapters_dir).resolve()

    if not chapters_dir.is_dir():
        print(f"Chapter directory not found: {chapters_dir}", file=sys.stderr)
        return 1

    chapter_files = get_chapter_files(chapters_dir)
    generated_links = generate_links(chapter_files, repo_root)

    if args.target == "-":
        print(generated_links)
        return 0

    target_path = (repo_root / args.target).resolve()
    if not target_path.is_file():
        print(f"Target markdown file not found: {target_path}", file=sys.stderr)
        return 1

    original_content = target_path.read_text(encoding="utf-8")
    updated_content = replace_between_markers(original_content, generated_links)
    target_path.write_text(updated_content, encoding="utf-8")
    print(f"Updated {target_path.relative_to(repo_root)}")

    if args.update_chapter_navs:
        update_all_chapter_navigation(chapter_files, repo_root)
        print(
            f"Updated chapter navigation in {len(chapter_files)} files under "
            f"{chapters_dir.relative_to(repo_root)}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
