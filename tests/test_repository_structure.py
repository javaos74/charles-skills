from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_every_skill_has_matching_frontmatter_name():
    skill_dirs = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
    assert skill_dirs, "repository must contain at least one skill"

    for skill_dir in skill_dirs:
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        name_line = next(
            line for line in frontmatter.splitlines() if line.startswith("name:")
        )
        assert name_line.partition(":")[2].strip().strip('"\'') == skill_dir.name
