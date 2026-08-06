"""Per-event converter skeleton.

Every event has different column names, sheet names, and per-event constants
(SFDC Campaign ID, Import Name, Import Owner, Initial Response Date). Copy
this file to convert_<event>_<YYYYMMDD>.py, fill the FIELD_MAP and
EVENT_CONSTANTS, and run.

The reference modules (name_splitter, company_resolver, enum_mappers,
template_writer) handle the invariant logic so this skeleton stays small.
"""
import argparse
import os
import sys

import pandas as pd

# Adjust the import path if you copy this file elsewhere.
sys.path.insert(0, os.path.dirname(__file__))
from company_resolver import load_company_index  # noqa: E402
from constants_extractor import build_event_constants  # noqa: E402
from enum_mappers import map_department, map_industry, map_job_level  # noqa: E402
from name_splitter import split_name  # noqa: E402
from phone_formatter import normalize_phone  # noqa: E402
from template_writer import (  # noqa: E402
    DEFAULT_COLUMN_MAP, load_template_enums, write_rows,
)


# ---- 1. EDIT: source schema for this event ----------------------------------
SOURCE_SHEET = 'Fusion2026Data'

# Optional event-specific company master sheet inside the SOURCE file. It only
# SUPPLEMENTS the bundled reference/company_mappings.xlsx (which is always the
# primary lookup). Set to None when the vendor export has no such sheet.
COMPANY_SHEET = 'CompanyNames'

# Map canonical Marketo concept -> source column name in SOURCE_SHEET.
FIELD_MAP = {
    'name': '성명',
    'email': '이메일',
    'phone': '연락처',
    'company_kr': '회사명',
    'company_en': '영문회사명',  # set to None if absent
    'department': '부서',
    'title': '직책(직급)',
    'channel': '유입경로',  # used to derive Requires Sales Follow-up
}

# Column names inside COMPANY_SHEET (the event supplement), when present.
COMPANY_KR_COL = '한글 회사명'
COMPANY_EN_COL = '영문 회사명'
COMPANY_INDUSTRY_COL = 'Industry'

# Fuzzy match acceptance (>= FUZZY_THRESHOLD) and nearest-name adoption
# (>= REVIEW_THRESHOLD, flagged for human review). Set REVIEW_THRESHOLD = 0 to
# always adopt the most similar known name instead of romanizing.
FUZZY_THRESHOLD = 88
REVIEW_THRESHOLD = 65

# ---- 2. EDIT: per-event constants ------------------------------------------
# Constants for 고정값-marked columns (template row 2) are pulled from the
# first data row of a prior filled result. Set PRIOR_RESULT to a previously
# completed Marketo import file for this event series.
PRIOR_RESULT = '1차 결과 Marketo Robot Import Lead Template_20260612.xlsx'

# Override or supplement the extracted constants. Values here take precedence
# and cover columns that aren't 고정값 but still need a per-row constant
# (e.g. Member Status when every attendee in the source is 'Attended').
EVENT_CONSTANTS_OVERRIDE = {
    'Member Status': 'Attended',
    'Channel Source': 'Live Event',
    'State': '',
    'Marketing Program': '',
    'Digital Asset': '',
}

# ---- 3. EDIT: Sales follow-up trigger ---------------------------------------
# Mark 'Requires Sales Follow-up' = Yes when ANY survey response in
# FOLLOW_UP_FIELDS contains ANY of FOLLOW_UP_KEYWORDS. Otherwise leave blank
# (per template marker: POC 요청, 미팅요청, 기업방문교육세션요청 = Yes;
# 자료요청, 아니오, 무응답 = blank).
#
# FOLLOW_UP_FIELDS lists source column names whose values should be scanned.
# Add survey-question columns here when the event roster includes them
# (e.g. 'POC신청 여부', '상담 요청', '세미나 신청'). Leave 자료요청 / brochure
# request columns OUT — those do not trigger follow-up.
FOLLOW_UP_FIELDS = ['유입경로']

FOLLOW_UP_KEYWORDS = [
    'POC', 'poc',
    '상담', '미팅', 'meeting',
    '세미나', '교육', '방문',
    '요청',  # broad fallback — note: '자료요청' must be handled by NEGATIVE list below
]

# Keywords that DISQUALIFY a row even if FOLLOW_UP_KEYWORDS matched.
# '자료요청' (asset request) is explicitly blank per the template marker.
FOLLOW_UP_NEGATIVE_KEYWORDS = ['자료요청', '자료 요청', '아니오', '무응답']


def build_row(src, company_index, event_constants,
              valid_industries, valid_job_levels, valid_departments,
              match_log=None):
    full_name = src.get(FIELD_MAP['name'], '')
    first, last = split_name(str(full_name or ''))

    kr_company = src.get(FIELD_MAP['company_kr'], '')
    src_en = src.get(FIELD_MAP['company_en']) if FIELD_MAP.get('company_en') else None
    # Primary lookup is reference/company_mappings.xlsx; unmatched 한글 회사명
    # fall back to the most similar known English name (flagged for review).
    match = company_index.resolve(
        kr_company, src_en,
        infer_industry_fn=lambda txt: map_industry(
            f"{kr_company} {src.get(FIELD_MAP['department'], '')} {src.get(FIELD_MAP['title'], '')}",
            valid_industries,
        ),
    )
    en_company, industry = match.company, match.industry
    if match_log is not None and match.needs_review:
        match_log.append(match)
    if industry is None or industry not in valid_industries:
        industry = map_industry(
            f"{kr_company} {src.get(FIELD_MAP['department'], '')} {src.get(FIELD_MAP['title'], '')}",
            valid_industries,
        )

    title = src.get(FIELD_MAP['title'], '')
    department = src.get(FIELD_MAP['department'], '')

    # Scan every FOLLOW_UP_FIELDS column. Positive keyword anywhere → Yes,
    # unless a negative keyword (e.g. '자료요청') overrides on that same field.
    follow_up = ''
    for field in FOLLOW_UP_FIELDS:
        text = str(src.get(field, '') or '')
        if not text:
            continue
        if any(neg in text for neg in FOLLOW_UP_NEGATIVE_KEYWORDS):
            continue
        if any(pos in text for pos in FOLLOW_UP_KEYWORDS):
            follow_up = 'Yes'
            break

    return {
        **event_constants,
        'Email Address': src.get(FIELD_MAP['email']),
        'Company Name': en_company,
        'First Name': first,
        'Last Name': last,
        'Job title': title,
        'Job Level': map_job_level(title, valid_job_levels),
        'Department': map_department(department, valid_departments),
        'Industry': industry,
        'Personal Contact Notes': f"{kr_company}/{department}/{title}",
        'Phone number': normalize_phone(src.get(FIELD_MAP['phone'])),
        'Requires Sales Follow-up': follow_up,
        'Company Name (Local)': kr_company,
    }


def main(input_file, output_file, template_file, prior_result=None):
    # Force phone column to string so vendor exports stored as int keep their
    # leading 0 (Excel int 1097676948 -> str '1097676948', then normalize).
    dtype_map = {FIELD_MAP['phone']: str} if FIELD_MAP.get('phone') else None
    df_source = pd.read_excel(input_file, sheet_name=SOURCE_SHEET, dtype=dtype_map)
    valid_industries, valid_job_levels, valid_departments = load_template_enums(template_file)

    # Bundled reference/company_mappings.xlsx is the primary company lookup.
    # COMPANY_SHEET, when present, only adds names the bundled file lacks.
    df_extra = (pd.read_excel(input_file, sheet_name=COMPANY_SHEET)
                if COMPANY_SHEET else None)
    company_index = load_company_index(
        extra_df=df_extra,
        extra_kr_col=COMPANY_KR_COL,
        extra_en_col=COMPANY_EN_COL,
        extra_industry_col=COMPANY_INDUSTRY_COL,
        fuzzy_threshold=FUZZY_THRESHOLD,
        review_threshold=REVIEW_THRESHOLD,
    )
    print(f'Company mappings loaded: {len(company_index)} names.')

    extracted = build_event_constants(template_file, prior_result) if prior_result else {}
    event_constants = {**extracted, **EVENT_CONSTANTS_OVERRIDE}
    print(f'Loaded {len(extracted)} constants from prior result; '
          f'{len(EVENT_CONSTANTS_OVERRIDE)} overrides applied.')
    missing = {'Country', 'Import Owner', 'Import Name', 'SFDC Campaign ID',
               'Initial Response Date'} - event_constants.keys()
    if missing:
        print(f'WARNING: missing per-event constants {missing}. '
              f'Add them to EVENT_CONSTANTS_OVERRIDE or pick a prior result that has them filled.')

    rows, skipped, match_log = [], [], []
    for idx, src in df_source.iterrows():
        if not src.get(FIELD_MAP['email']) or pd.isna(src.get(FIELD_MAP['email'])):
            skipped.append(idx)
            continue
        rows.append(build_row(
            src.to_dict(), company_index, event_constants,
            valid_industries, valid_job_levels, valid_departments,
            match_log=match_log,
        ))

    write_rows(template_file, output_file, rows, column_map=DEFAULT_COLUMN_MAP)
    print(f'Processed {len(rows)} rows. Saved to {output_file}')
    if skipped:
        print(f'Skipped {len(skipped)} rows (missing email): {skipped[:10]}{"..." if len(skipped) > 10 else ""}')
    if match_log:
        # Company names only — no email / phone (PII stays out of the log).
        print(f'Company names needing review: {len(match_log)}')
        for m in match_log:
            score = f' {m.score}' if m.score else ''
            matched = f' (matched {m.matched_kr})' if m.matched_kr else ''
            print(f'  [{m.method}{score}] {m.query} -> {m.company}{matched}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('-t', '--template', required=True)
    parser.add_argument(
        '-p', '--prior-result', default=PRIOR_RESULT,
        help='Path to a prior filled Marketo import file. 고정값-marked columns '
             'are pulled from its first data row.',
    )
    args = parser.parse_args()
    if not os.path.exists(args.input):
        print(f'Input not found: {args.input}'); sys.exit(1)
    if not os.path.exists(args.template):
        print(f'Template not found: {args.template}'); sys.exit(1)
    if args.prior_result and not os.path.exists(args.prior_result):
        print(f'Prior result not found: {args.prior_result}'); sys.exit(1)
    main(args.input, args.output, args.template, args.prior_result)
