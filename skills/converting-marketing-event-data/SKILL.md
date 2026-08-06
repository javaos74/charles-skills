---
name: converting-marketing-event-data
description: "Convert post-event attendee data into the Marketo Robot Import Lead Template (xlsx). Source format varies per event vendor — first inspect columns, then assemble a per-event converter from reusable reference snippets (name split, company resolver, enum mappers, template writer). Splits Korean/English names into First/Last, maps free-text 직책/부서/회사 to Marketo's allowed Job Level / Industry / Department values, and resolves 한글 회사명 → 영문 회사명 with fuzzy fallback. Use when the user mentions Marketo import, or asks to fill the blue-header columns of a Marketo Robot Import Lead Template."
when_to_use: "User has a marketing event attendee Excel and wants it converted into the Marketo Robot Import Lead Template format. Triggers: 'Marketo 템플릿', 'Marketo import', '이벤트 데이터 변환', 'lead 업로드 파일 만들어', '리드 임포트 파일', or running against files matching 'Marketo Robot Import Lead Template*.xlsx'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
model: sonnet
user-invocable: true
---
# Converting Marketing Event Data → Marketo Import Template

Convert a post-event attendee roster (Korean + English mixed) into a Marketo Robot Import Lead Template `.xlsx` ready to upload.

> **Source format varies per event.** Each vendor exports columns differently (`성명` vs `이름` vs `참가자명`, `직책` vs `직급` vs `직위`, separate vs merged sheets). DO NOT assume the column names from a previous event apply. Always inspect first, propose a mapping, confirm with the user, then assemble a per-event converter from `reference/`.

## Critical Rules

1. **Inspect before converting.** Run `reference/source_inspector.py` against the source file to enumerate sheets, columns, and a suggested canonical mapping. Confirm the proposed `FIELD_MAP` with the user before writing the converter.
2. **Never edit `reference/` files for one-off event quirks.** Reference modules hold invariant logic (name splitting, fuzzy company match, openpyxl write). Per-event differences belong in a fork of `converter_skeleton.py` named `convert_<event>_<YYYYMMDD>.py`.
3. **Preserve template formatting.** Always use `template_writer.write_rows` (openpyxl). Never `pandas.to_excel` — it strips the blue header styles.
4. **Validate enum columns against the template's `Fields` sheet.** Industry / Job Level / Department must match a value from `Fields`. Defaults are allowed; free-text is not. `enum_mappers` enforces this.
5. **Process every input row.** Skip silently only when email is missing; log skipped indices and surface the count at end.
6. **Pull constants from a prior filled result, not from typed-in values.** Columns marked `고정값`, `행사명 영문`, `행사 날짜`, `마케팅 제공`, or `드롭다운` in the template's row 2 are per-event constants. Use `constants_extractor.build_event_constants(template, prior_result)` to read them from the first data row of a previously completed Marketo import file. Confirm with the user when no prior result exists for this event series, or when the warning surfaces missing required constants (`Country`, `Import Owner`, `Import Name`, `SFDC Campaign ID`, `Initial Response Date`).
7. **Use the existing venv if available.** `./venv/bin/python`. Required packages already installed: `pandas`, `openpyxl`, `thefuzz`, `korean_romanizer`.
8. **Never log full rows.** Log row index + email only. Phone numbers and emails are PII.
9. **Phone column must be Text format.** Run every phone value through `phone_formatter.normalize_phone` (strip non-digits, restore leading 0 for Korean mobile prefixes 01x/07x) AND ensure `template_writer.write_rows` applies `number_format='@'` to the `Phone number` column (default behavior via `TEXT_COLUMNS`). Without both, Excel re-parses the digit string as a number on open and `01097676948` becomes `1097676948`. Also force `dtype=str` on the source phone column when reading via `pd.read_excel` so int-typed exports do not lose the leading 0 before normalization.
10. **`Requires Sales Follow-up` is a survey-response signal, not a UTM channel.** Set `Yes` only when the source row contains an explicit POC / 상담 / 미팅 / 세미나 / 기업방문교육 / 방문 request from a survey-question column. Leave blank for `자료요청`, `아니오`, `무응답`, and any UTM/utm_source-style channel field (e.g. `유입경로` values like `metaad1fb`, `uipath03`). In `convert_<EVENT>_<YYYYMMDD>.py`, list survey-question source columns in `FOLLOW_UP_FIELDS`. Do NOT point `FOLLOW_UP_FIELDS` at a UTM channel column. If the source has no survey column for this event, leave the list empty — every row will be blank, which is correct.

## Workflow

### Step 1 — Locate inputs

```bash
ls *.xlsx
```

Identify three files. Ask the user only when ambiguous.

| Input       | How to identify                                                                                                                     |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Source data | Vendor export (e.g.`Fusion2026Data.xlsx`).                                                                                        |
| Template    | `Marketo Robot Import Lead Template_*.xlsx`. Prefer the `_가이드 추가_` version when present (has `Fields` sheet documented). |
| Output      | `Marketo Robot Import Lead Template_<EVENT>_<YYYYMMDD>.xlsx`.                                                                     |

### Step 2 — Inspect source schema

```bash
./venv/bin/python <SKILL_DIR>/reference/source_inspector.py <SOURCE_XLSX>
```

The inspector lists every sheet, its columns, a sample row, and a suggested `FIELD_MAP` keyed by canonical concept (`name`, `email`, `company_kr`, `title`, etc.). Show the proposal to the user via `AskUserQuestion` if any canonical concept is missing or ambiguous.

### Step 3 — Inspect template enums

```bash
./venv/bin/python -c "import pandas as pd; \
  f = pd.read_excel('<TEMPLATE>', sheet_name='Fields'); \
  print('Industries:', f['Industry'].dropna().tolist()); \
  print('JobLevels:', f['Job Level'].dropna().tolist()); \
  print('Departments:', f['Department'].dropna().tolist())"
```

If the template revision differs (column shifts, renamed sheet), update the call-site `column_map` argument to `template_writer.write_rows` — do not edit `template_writer.py`.

### Step 4 — Assemble per-event converter

Copy the skeleton and edit three sections:

```bash
cp <SKILL_DIR>/reference/converter_skeleton.py \
   convert_<EVENT>_<YYYYMMDD>.py
```

Edit:

1. `SOURCE_SHEET` / `COMPANY_SHEET` / `FIELD_MAP` — match what `source_inspector.py` reported.
2. `PRIOR_RESULT` — path to a previously filled Marketo import file for this event series. The skeleton calls `constants_extractor.build_event_constants(template, prior_result)` to populate `고정값`-marked columns from its first data row. If none exists, fill `EVENT_CONSTANTS_OVERRIDE` after confirming each value with the user.
3. `EVENT_CONSTANTS_OVERRIDE` — values that take precedence over the extracted constants (e.g. `Member Status`, `Channel Source`, blanks).
4. `FOLLOW_UP_FIELDS` — list of source columns that hold survey responses (POC/상담/미팅/세미나 requests). Per Critical Rule 10, do NOT include UTM channel columns. Leave empty when the source has no survey column.
5. `FOLLOW_UP_KEYWORDS` / `FOLLOW_UP_NEGATIVE_KEYWORDS` — extend only when the survey introduces new request phrasings. The defaults already cover POC/상담/미팅/세미나/교육/방문/요청 and exclude 자료요청/아니오/무응답.

If the source has no separate company master sheet, replace the `df_companies = pd.read_excel(...)` line with an empty DataFrame and skip company resolution; rely on source `영문회사명` + romanization.

### Step 5 — Run conversion

```bash
./venv/bin/python convert_<EVENT>_<YYYYMMDD>.py \
  <SOURCE_XLSX> \
  <OUTPUT_XLSX> \
  -t <TEMPLATE_XLSX> \
  -p <PRIOR_FILLED_RESULT_XLSX>
```

Expected stdout:

```
Loaded <N> constants from prior result; <M> overrides applied.
Processed <N> rows. Saved to <OUTPUT_XLSX>
```

If a `WARNING: missing per-event constants {...}` line appears, the prior result has empty cells for required 고정값 columns. Either pick a different prior result (e.g. the `_가이드 추가_` template's sample row) or add the missing values to `EVENT_CONSTANTS_OVERRIDE`.

### Step 6 — Verify output

```bash
./venv/bin/python -c "import openpyxl; \
  wb = openpyxl.load_workbook('<OUTPUT_XLSX>'); ws = wb['Sheet1']; \
  rows = [[c.value for c in r] for r in ws.iter_rows(min_row=5, max_row=8)]; \
  [print(r[:6], r[18:22]) for r in rows]"
```

Confirm:

- First six columns (Email / Company / First / Last / Country / State) populated.
- Job title / Job Level / Department / Industry populated and on-list.
- No row has both `First Name` and `Last Name` blank when `성명` or `이름` was present.

If any enum is blank or off-list, fix the keyword table in `reference/enum_mappers.py` (only safe when the fix is broadly applicable across events) or add an event-specific override in your `convert_<EVENT>_<YYYYMMDD>.py`.

## Reference Navigation

| File                                 | Purpose                                                                                                                                                                              | Edit per event?    |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------ |
| `reference/source_inspector.py`    | List sheets/columns and propose canonical FIELD_MAP.                                                                                                                                 | No                 |
| `reference/name_splitter.py`       | `split_name(full_name)` → (first, last). Handles Korean (positional split + 2-char surnames), English (whitespace + CamelCase).                                                   | No                 |
| `reference/company_resolver.py`    | `resolve_company(...)` with exact → fuzzy → source-en → romanize fallback chain.                                                                                                | No                 |
| `reference/enum_mappers.py`        | `map_industry`, `map_job_level`, `map_department` against the template's `Fields` sheet. Edit keyword tables only when adding broadly applicable terms.                      | Rarely             |
| `reference/template_writer.py`     | `load_template_enums`, `write_rows`. Pass a custom `column_map` if your template revision differs. Forces `Phone number` to Text format via `TEXT_COLUMNS`.                | No                 |
| `reference/phone_formatter.py`     | `normalize_phone(value)` — strip non-digits, restore leading 0 for Korean mobile (01x, 11/16/17/18/19) when source exports phones as int.                                         | No                 |
| `reference/constants_extractor.py` | `detect_constant_columns(template)` + `build_event_constants(template, prior_result)`. Reads 고정값-marked columns (template row 2) from a prior filled result's first data row. | No                 |
| `reference/converter_skeleton.py`  | Copy →`convert_<EVENT>_<YYYYMMDD>.py`. Edit FIELD_MAP, PRIOR_RESULT, EVENT_CONSTANTS_OVERRIDE, FOLLOW_UP_FIELDS, FOLLOW_UP_KEYWORDS, FOLLOW_UP_NEGATIVE_KEYWORDS.                                                                | Yes — every event |

## Anti-patterns

- **Do not** hardcode column names like `성명` / `회사명` in your converter. Read them via `FIELD_MAP[concept]` so a vendor with `이름` / `소속` works without code changes.
- **Do not** use `pd.to_excel(...)` — strips blue header formatting. Always use `template_writer.write_rows`.
- **Do not** romanize when the source row has `영문회사명` filled — `company_resolver` already prefers it.
- **Do not** map `책임` / `선임` to `Director`. Both are `Manager` per the keyword table.
- **Do not** emit free-text `Industry` (e.g. `Telco`, `Finance`). Only literal strings from `Fields.Industry`.
- **Do not** silently skip rows. Email-missing skips must surface in the final summary line.
- **Do not** write phone numbers as raw `int`s or to a cell with `General` format. Always normalize via `phone_formatter.normalize_phone` AND let `template_writer.write_rows` apply `number_format='@'` (Text). Either alone is insufficient — Excel will silently strip the leading 0 on open even when the in-memory cell value is correct.
- **Do not** retype 고정값 column values (`Country`, `Import Owner`, `Channel Team`, etc.) into `EVENT_CONSTANTS_OVERRIDE` when a prior filled result exists. Set `PRIOR_RESULT` and let `constants_extractor` pull them from row 5 — fewer typos, fewer drift sources.
- **Do not** reuse a prior result from a different event series without re-confirming `SFDC Campaign ID`, `Import Name`, and `Initial Response Date`. These change every event even when other constants are stable.
- **Do not** trigger `Requires Sales Follow-up = Yes` from a UTM channel column (`유입경로`, `초청경로`, etc.). UTM values like `metaad1fb` or `uipath03` say nothing about whether the lead asked for a sales conversation. Only survey-response columns (POC 신청 여부, 상담 요청, 세미나 신청, 기업방문교육 요청 등) qualify.
- **Do not** mark `자료요청` / `자료 요청` (asset/brochure download request) as follow-up. The template marker explicitly excludes it — those leads want collateral, not a salesperson.
