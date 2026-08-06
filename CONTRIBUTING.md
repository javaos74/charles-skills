# Contributing

## Add a skill

1. Create `skills/<skill-name>/` using lowercase letters, digits, and hyphens.
2. Add `SKILL.md`; its frontmatter `name` must exactly match the folder name.
3. Keep reusable executable Python in `reference/` or `scripts/`, examples in `examples/`, and tests in `tests/`.
4. Put runtime dependencies in the skill's own `requirements.txt`. Put repository-only tooling in the root `requirements-dev.txt`.
5. Do not make one skill import another skill. Move truly shared code to a versioned package or duplicate a small stable helper so each skill remains independently installable.
6. Never commit real attendee, customer, or campaign data. Use anonymized fixtures only.
7. Add the skill to the root README table.

## Validate

```bash
python scripts/validate-repo.py
python -m pytest
```

The repository validator checks folder naming, `SKILL.md` presence, frontmatter names, and accidental nested repository documentation.
