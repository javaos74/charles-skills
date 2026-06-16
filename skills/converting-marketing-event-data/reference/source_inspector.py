"""Inspect an unknown event source workbook and propose a column mapping.

Each event uses a different vendor's Excel export — column names vary
(성명 vs 이름 vs 참가자명, 회사명 vs 소속 vs 회사, 직책 vs 직급 vs 직위, etc.).
Run this BEFORE writing the per-event converter so you know which source
columns feed which Marketo fields.

Usage:
    python source_inspector.py <SOURCE_XLSX>
"""
import sys

import pandas as pd


# Heuristic synonym map: source-column-substring -> canonical Marketo concept.
# Treat as suggestions; always confirm with the user before committing.
SYNONYMS = {
    'name': ['성명', '이름', '참가자명', '참석자명', '성함', 'name'],
    'email': ['이메일', '메일', 'email', 'e-mail','e메일', '업무용 이메일', '업무용 email'],
    'phone': ['연락처', '전화', '휴대폰', '핸드폰', 'phone', 'mobile', 'tel'],
    'company_kr': ['회사명', '소속', '회사', '기관명', 'company'],
    'company_en': ['영문회사명', 'company name (en)', 'english company', '영문회사'],
    'department': ['부서', '팀', '본부', 'department', 'dept', 'team'],
    'title': ['직책', '직급', '직위', 'title', 'position', 'role'],
    'channel': ['유입경로', '신청경로', '경로', 'channel', 'source'],
}


def list_sheets(path):
    return pd.ExcelFile(path).sheet_names


def propose_mapping(columns):
    proposal = {}
    cols_lower = [(c, str(c).lower()) for c in columns]
    for canonical, synonyms in SYNONYMS.items():
        for original, lower in cols_lower:
            if any(s in lower for s in synonyms):
                proposal[canonical] = original
                break
    return proposal


def inspect(path):
    sheets = list_sheets(path)
    print(f'Sheets: {sheets}')
    for sheet in sheets:
        df = pd.read_excel(path, sheet_name=sheet, nrows=3)
        print(f'\n--- {sheet} ---')
        print(f'Columns: {df.columns.tolist()}')
        print(f'Sample row: {df.iloc[0].to_dict() if not df.empty else "empty"}')
        proposal = propose_mapping(df.columns.tolist())
        if proposal:
            print(f'Suggested mapping: {proposal}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python source_inspector.py <SOURCE_XLSX>')
        sys.exit(1)
    inspect(sys.argv[1])
