# converting-marketing-event-data

A Claude Code skill that converts post-event attendee rosters (Excel) into the **Marketo Robot Import Lead Template** format. Designed for Korean B2B marketing events where the source roster mixes Korean/English names, free-text job titles, and Korean company names that must be resolved to canonical English ones.

## What it does

Takes an event attendee Excel and produces an upload-ready Marketo lead import file:

- Splits Korean names (`송미건` → first=`미건`, last=`송`) including 2-character surnames (`남궁`, `황보`, etc.) and English names (`John Doe` / CamelCase).
- Resolves `한글 회사명` → `영문 회사명` via a master sheet with **exact → fuzzy (≥80) → source-en → romanize** fallback chain.
- Maps free-text `직책` / `부서` / industry signals to the template's `Fields` sheet allowed values (Job Level, Department, Industry).
- Pulls per-event constants (Country, Import Owner, SFDC Campaign ID, etc.) from the first data row of a prior filled result instead of being retyped.
- Normalizes phone numbers (restores leading 0 lost on int-typed exports) and writes them as Excel Text format so the leading 0 survives reopening.
- Flags `Requires Sales Follow-up = Yes` only when a survey-response column contains a POC / 상담 / 미팅 / 세미나 / 기업방문교육 request.

## Repository structure

```
converting-marketing-event-data/
├── SKILL.md                  # Skill definition (loaded by Claude Code)
├── README.md                 # This file
├── LICENSE                   # MIT
├── requirements.txt          # Python deps
├── reference/                # Reusable, invariant logic — DO NOT edit per event
│   ├── source_inspector.py
│   ├── name_splitter.py
│   ├── company_resolver.py
│   ├── enum_mappers.py
│   ├── template_writer.py
│   ├── phone_formatter.py
│   ├── constants_extractor.py
│   └── converter_skeleton.py # Copy → convert_<EVENT>_<YYYYMMDD>.py and edit
├── examples/                 # Anonymized sample data
└── tests/                    # Unit tests
```

## Install (Claude Code)

```bash
git clone https://github.com/<you>/converting-marketing-event-data.git \
  ~/.claude/skills/converting-marketing-event-data
```

Or per-project:

```bash
cd <your-project>
git clone https://github.com/<you>/converting-marketing-event-data.git \
  .claude/skills/converting-marketing-event-data
```

Restart Claude Code. The skill auto-loads when you mention `Marketo 템플릿`, `Marketo import`, `이벤트 데이터 변환`, etc.

## Install (standalone Python)

```bash
git clone https://github.com/<you>/converting-marketing-event-data.git
cd converting-marketing-event-data
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Quick Start

```bash
# 1. Inspect the source schema (proposes a canonical FIELD_MAP)
./venv/bin/python reference/source_inspector.py examples/sample_source.xlsx

# 2. Copy the skeleton and edit FIELD_MAP / PRIOR_RESULT / FOLLOW_UP_FIELDS
cp reference/converter_skeleton.py convert_myevent_20260616.py
# (edit per Step 4 in SKILL.md)

# 3. Run the conversion
./venv/bin/python convert_myevent_20260616.py \
  examples/sample_source.xlsx \
  output.xlsx \
  -t examples/sample_template.xlsx \
  -p examples/sample_prior_result.xlsx
```

Expected stdout:

```
Loaded N constants from prior result; M overrides applied.
Processed K rows. Saved to output.xlsx
```

See `SKILL.md` for the full workflow, critical rules, and anti-patterns.

## Per-event customization

Per-event differences belong in your `convert_<EVENT>_<YYYYMMDD>.py` fork — never edit `reference/`. Five things change per event:

1. `FIELD_MAP` — source column names (vendor exports vary).
2. `PRIOR_RESULT` — path to a previously filled Marketo file for this event series.
3. `EVENT_CONSTANTS_OVERRIDE` — values that supplement / override the extracted constants.
4. `FOLLOW_UP_FIELDS` — survey-response columns that drive `Requires Sales Follow-up`.
5. `FOLLOW_UP_KEYWORDS` / `FOLLOW_UP_NEGATIVE_KEYWORDS` — extend only when the survey introduces new phrasings.

## Data privacy

Real attendee rosters contain PII (names, emails, phone numbers). The repo's `.gitignore` excludes all `*.xlsx` files outside `examples/`. **Do not commit real event data.** Use the anonymized files in `examples/` for testing.

## Limitations

- Optimized for Korean B2B events. Non-Korean rosters work but lose the Korean-specific company resolution and name-split heuristics.
- Industry / Job Level / Department keyword tables are tuned for technology / enterprise audiences. Adjust `reference/enum_mappers.py` if your event audience differs.
- Template column indices in `template_writer.DEFAULT_COLUMN_MAP` are pinned to the Marketo Robot Import Lead Template revision dated 2026-06. If Marketing publishes a new template revision with shifted columns, pass a custom `column_map` to `write_rows`.

## License

MIT. See [LICENSE](LICENSE).
