#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path


START_MARKER = "<!-- chapter-links:start -->"
END_MARKER = "<!-- chapter-links:end -->"


def generate_links(chapters_dir: Path, base_dir: Path) -> str:
    chapter_files = sorted(
        path for path in chapters_dir.iterdir() if path.is_file() and path.suffix == ".md"
    )
    lines = []
    for path in chapter_files:
        relative_path = path.relative_to(base_dir).as_posix()
        title = path.stem
        lines.append(f"- [{title}](./{relative_path})")
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
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    chapters_dir = (repo_root / args.chapters_dir).resolve()

    if not chapters_dir.is_dir():
        print(f"Chapter directory not found: {chapters_dir}", file=sys.stderr)
        return 1

    generated_links = generate_links(chapters_dir, repo_root)

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
