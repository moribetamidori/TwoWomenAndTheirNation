#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


FILENAME_PATTERN = re.compile(r"^(?P<number>\d{2})-(?P<rest>.+)\.md$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "One-time renumbering utility for chapter files. "
            "By default, chapters 21-70 become 22-71."
        )
    )
    parser.add_argument(
        "--chapters-dir",
        default="manuscript/chapters",
        help="Directory containing chapter markdown files.",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=20,
        help="Only renumber chapters with a number greater than this value.",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=70,
        help="Only renumber chapters with a number less than or equal to this value.",
    )
    parser.add_argument(
        "--delta",
        type=int,
        default=1,
        help="Amount to add to each matching chapter number.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned changes without modifying any files.",
    )
    parser.add_argument(
        "--skip-readme",
        action="store_true",
        help="Do not refresh README chapter links after renaming.",
    )
    return parser.parse_args()


def collect_renames(chapters_dir: Path, start: int, end: int, delta: int) -> list[tuple[int, Path, Path]]:
    renames: list[tuple[int, Path, Path]] = []

    for path in chapters_dir.iterdir():
        if not path.is_file() or path.suffix != ".md":
            continue

        match = FILENAME_PATTERN.match(path.name)
        if not match:
            continue

        number = int(match.group("number"))
        if not (start < number <= end):
            continue

        new_number = number + delta
        new_name = f"{new_number:02d}-{match.group('rest')}.md"
        renames.append((number, path, path.with_name(new_name)))

    return sorted(renames, key=lambda item: item[0], reverse=True)


def validate_renames(renames: list[tuple[int, Path, Path]]) -> None:
    source_paths = {source for _, source, _ in renames}

    for old_number, source, target in renames:
        if source == target:
            raise ValueError(f"No-op rename detected for {source.name}")
        if target.exists() and target not in source_paths:
            raise ValueError(
                f"Cannot rename {source.name} to {target.name}: target already exists."
            )
        if old_number >= 100 or old_number < 0:
            raise ValueError(f"Chapter number out of supported range: {old_number}")


def update_heading(path: Path, old_number: int, new_number: int) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    old_prefix = f"{old_number:02d}-"
    new_prefix = f"{new_number:02d}-"
    pattern = re.compile(rf"^(?P<prefix>\s*#\s*)?{re.escape(old_prefix)}")

    for index, line in enumerate(lines[:5]):
        if not pattern.match(line):
            continue
        lines[index] = pattern.sub(
            lambda match: f"{match.group('prefix') or ''}{new_prefix}",
            line,
            count=1,
        )
        path.write_text("".join(lines), encoding="utf-8")
        return


def refresh_readme(repo_root: Path) -> None:
    script_path = repo_root / "scripts" / "update_chapter_links.py"
    subprocess.run([sys.executable, str(script_path)], check=True, cwd=repo_root)


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    chapters_dir = (repo_root / args.chapters_dir).resolve()

    if not chapters_dir.is_dir():
        print(f"Chapter directory not found: {chapters_dir}", file=sys.stderr)
        return 1

    renames = collect_renames(chapters_dir, args.start, args.end, args.delta)
    if not renames:
        print("No matching chapter files found.")
        return 0

    try:
        validate_renames(renames)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    for old_number, source, target in renames:
        print(f"{source.name} -> {target.name}")

    if args.dry_run:
        print("Dry run only; no files were changed.")
        return 0

    for old_number, source, target in renames:
        source.rename(target)
        update_heading(target, old_number=old_number, new_number=old_number + args.delta)

    if not args.skip_readme:
        refresh_readme(repo_root)

    print("Renumbering complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
