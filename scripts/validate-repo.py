#!/usr/bin/env python3
"""Validate the structure of every skill in this repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
VALID_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"

    if not VALID_NAME.fullmatch(skill_dir.name):
        errors.append(f"{skill_dir}: invalid skill folder name")
    if not skill_file.is_file():
        return errors + [f"{skill_dir}: missing SKILL.md"]

    content = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return errors + [f"{skill_file}: missing YAML frontmatter"]

    metadata = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip('"\'')

    if metadata.get("name") != skill_dir.name:
        errors.append(
            f"{skill_file}: name {metadata.get('name')!r} does not match folder"
        )
    if not metadata.get("description"):
        errors.append(f"{skill_file}: missing description")

    for filename in ("README.md", "LICENSE", ".gitignore"):
        if (skill_dir / filename).exists():
            errors.append(
                f"{skill_dir / filename}: move repository-level files to the root"
            )
    return errors


def main() -> int:
    skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())
    if not skill_dirs:
        print("No skill directories found", file=sys.stderr)
        return 1

    errors = [error for path in skill_dirs for error in validate_skill(path)]
    if errors:
        print("Repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(skill_dirs)} skill(s):")
    for path in skill_dirs:
        print(f"- {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
