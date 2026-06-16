"""Map free-text 직책 / 부서 / 회사 info to Marketo's allowed enum values.

The template's `Fields` sheet enumerates valid values for Industry, Job Level,
Department. These mappers must always return a value present in that sheet —
never free-text. Update the keyword tables when an event roster contains
roles or industries the current keyword set misses.
"""

INDUSTRY_KEYWORDS = {
    'Banking and Financial Services': ['은행', '금융', '투자', '증권', '카드', '캐피탈', 'bank', 'finance'],
    'Energy and Utilities': ['에너지', '전력', '발전', '가스', '수도', '석유', 'energy'],
    'Entertainment and Media': ['게임', '미디어', '엔터', '방송', '신문', '영화', 'game', 'media'],
    'Healthcare': ['병원', '의료', '제약', '바이오', '건강', 'health', 'bio'],
    'Insurance': ['보험', '화재', '생명보험', 'insurance'],
    'Life Sciences': ['생명과학', '유전'],
    'Logistics': ['물류', '운송', '택배', '유통', 'logistics'],
    'Manufacturing': ['제조', '생산', '공장', '전자', '자동차', '중공업', '화학', '철강', 'manufacturing'],
    'Professional Services': ['컨설팅', '회계', '법무', 'professional'],
    'Public Sector': ['공공', '정부', '공사', '기관', '시청', '구청', 'public'],
    'Retail': ['리테일', '판매', '쇼핑', 'retail', 'commerce'],
    'Technology': ['기술', 'IT', '소프트웨어', '테크', '시스템', '네트워크', 'technology', 'soft'],
    'Telecommunications': ['통신', '텔레콤', 'sk telecom', 'kt ', 'lgu+', 'telecom'],
}

# Order matters: more senior keywords must be checked before junior ones.
JOB_LEVEL_KEYWORDS = [
    ('Executive/ C-Level', ['ceo', 'cto', 'cio', 'cfo', '대표', '임원', '상무', '전무', '사장', '부사장']),
    ('Vice President', ['vp', 'vice president', '본부장']),
    ('Director', ['director', '이사', '실장', '처장']),
    ('Manager', ['manager', '팀장', '부장', '차장', '과장', '책임', '선임']),
    ('Individual Contributor', ['staff', 'engineer', '대리', '계장', '사원', '주임', '연구원', '행정원']),
    ('Student', ['student', '학생']),
]


def _pick(default, valid_list):
    return default if default in valid_list else (valid_list[0] if valid_list else default)


def map_industry(source_text, valid_industries):
    text = str(source_text or '').lower()
    for industry, keys in INDUSTRY_KEYWORDS.items():
        if industry not in valid_industries:
            continue
        if any(k in text for k in keys):
            return industry
    return _pick('Technology', valid_industries)


def map_job_level(title, valid_job_levels):
    text = str(title or '').lower()
    for level, keys in JOB_LEVEL_KEYWORDS:
        if level not in valid_job_levels:
            continue
        if any(k in text for k in keys):
            return level
    return _pick('Individual Contributor', valid_job_levels)


def map_department(department, valid_departments):
    text = str(department or '').lower()
    for d in valid_departments:
        if d.lower() in text:
            return d
    return _pick('IT', valid_departments)
