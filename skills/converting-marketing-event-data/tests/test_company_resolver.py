"""Tests for company_resolver — covers exact match, fuzzy fallback,
source-en preference, and romanize last resort."""
import pandas as pd
import pytest

from company_resolver import (
    build_company_maps, resolve_company, romanize_korean,
)


@pytest.fixture
def df_companies():
    return pd.DataFrame([
        {'한글 회사명': '예시전자',     '영문 회사명': 'Example Electronics', 'Industry': 'Manufacturing'},
        {'한글 회사명': '샘플은행',     '영문 회사명': 'Sample Bank',         'Industry': 'Banking and Financial Services'},
        {'한글 회사명': '데모헬스케어', '영문 회사명': 'Demo Healthcare',     'Industry': 'Healthcare'},
    ])


@pytest.fixture
def maps(df_companies):
    return build_company_maps(df_companies)


def _infer_default(text):
    return 'Technology'


def test_exact_match(df_companies, maps):
    company_map, industry_map = maps
    en, ind = resolve_company('예시전자', None, df_companies, company_map, industry_map, _infer_default)
    assert en == 'Example Electronics'
    assert ind == 'Manufacturing'


def test_fuzzy_match_above_threshold(df_companies, maps):
    company_map, industry_map = maps
    # '샘플 은행' (with space) should fuzzy-match '샘플은행'.
    en, ind = resolve_company('샘플 은행', None, df_companies, company_map, industry_map, _infer_default)
    assert en == 'Sample Bank'
    assert ind == 'Banking and Financial Services'


def test_no_match_uses_source_english(df_companies, maps):
    company_map, industry_map = maps
    en, ind = resolve_company('완전히새로운회사', 'Brand New Co', df_companies,
                              company_map, industry_map, _infer_default)
    assert en == 'Brand New Co'
    assert ind == 'Technology'  # from infer_default


def test_no_match_no_source_english_romanizes(df_companies, maps):
    company_map, industry_map = maps
    en, ind = resolve_company('테스트물류', None, df_companies,
                              company_map, industry_map, _infer_default)
    assert en  # non-empty romanized output
    assert en[0].isupper()  # Title cased
    assert ind == 'Technology'


def test_empty_company_name(df_companies, maps):
    company_map, industry_map = maps
    en, ind = resolve_company('', None, df_companies, company_map, industry_map, _infer_default)
    assert en == ''
    assert ind is None


@pytest.mark.parametrize('value, contains_letter', [
    ('삼성전자', True),
    ('Samsung', True),  # already English, returned unchanged-ish
])
def test_romanize_korean_returns_string(value, contains_letter):
    result = romanize_korean(value)
    assert isinstance(result, str)
    assert len(result) > 0
