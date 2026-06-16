"""Tests for enum_mappers — verifies keyword tables resolve to template-valid
values and that priority ordering for Job Level is correct (senior beats junior)."""
import pytest

from enum_mappers import map_department, map_industry, map_job_level


VALID_INDUSTRIES = [
    'Banking and Financial Services', 'Healthcare', 'Manufacturing',
    'Retail', 'Technology', 'Telecommunications', 'Public Sector', 'Insurance',
]
VALID_JOB_LEVELS = [
    'Executive/ C-Level', 'Vice President', 'Director', 'Manager',
    'Individual Contributor', 'Student',
]
VALID_DEPARTMENTS = ['IT', 'Marketing', 'Sales', 'HR', 'Engineering']


@pytest.mark.parametrize('text, expected', [
    ('삼성전자 메모리 반도체', 'Manufacturing'),
    ('우리은행 카드사업부 차장', 'Banking and Financial Services'),
    ('LG U+ 통신팀', 'Telecommunications'),
    ('서울아산병원 의료진', 'Healthcare'),
    ('서울시청 공공기관', 'Public Sector'),
])
def test_map_industry_keyword_match(text, expected):
    assert map_industry(text, VALID_INDUSTRIES) == expected


def test_map_industry_default_when_no_match():
    # 'Technology' is in valid list and is the default.
    assert map_industry('완전히 무관한 텍스트', VALID_INDUSTRIES) == 'Technology'


def test_map_industry_default_falls_back_to_first_when_technology_missing():
    no_tech = ['Healthcare', 'Manufacturing']
    assert map_industry('xyz', no_tech) == 'Healthcare'


@pytest.mark.parametrize('title, expected', [
    ('대표이사', 'Executive/ C-Level'),
    ('CEO', 'Executive/ C-Level'),
    ('본부장', 'Vice President'),
    ('이사', 'Director'),
    ('팀장', 'Manager'),
    ('책임 연구원', 'Manager'),       # 책임 → Manager (NOT Director)
    ('선임 매니저', 'Manager'),       # 선임 → Manager
    ('대리', 'Individual Contributor'),
    ('학생', 'Student'),
])
def test_map_job_level(title, expected):
    assert map_job_level(title, VALID_JOB_LEVELS) == expected


def test_map_job_level_priority_executive_beats_manager():
    # '대표' (Executive) appears earlier than '팀장' (Manager) in title — must
    # pick Executive because the keyword list is ordered by seniority.
    assert map_job_level('대표 겸 팀장', VALID_JOB_LEVELS) == 'Executive/ C-Level'


def test_map_job_level_default():
    assert map_job_level('알수없음', VALID_JOB_LEVELS) == 'Individual Contributor'


@pytest.mark.parametrize('dept, expected', [
    ('IT 인프라팀', 'IT'),
    ('Marketing Team', 'Marketing'),
    ('Sales Operations', 'Sales'),
    ('HR business partner', 'HR'),
])
def test_map_department(dept, expected):
    # Substring match against valid_departments. Korean department text does
    # not translate — '마케팅' != 'Marketing'. Add explicit Korean keyword
    # mapping in enum_mappers.py if your event needs it.
    assert map_department(dept, VALID_DEPARTMENTS) == expected


def test_map_department_korean_falls_back_to_default():
    # '마케팅' has no English keyword in VALID_DEPARTMENTS — falls back to 'IT'.
    assert map_department('마케팅 본부', VALID_DEPARTMENTS) == 'IT'


def test_map_department_default():
    assert map_department('알수없는부서', VALID_DEPARTMENTS) == 'IT'
