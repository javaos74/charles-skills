"""Resolve a Korean company name to (English Name, Industry).

Resolution order (do not skip steps):
  1. Exact match against the CompanyNames master sheet.
  2. Fuzzy match (token_set_ratio >= 80) against the master sheet.
  3. Source row's own 영문회사명 if present.
  4. Romanize the Korean name; infer Industry from 회사명 + 부서 + 직책.

The CompanyNames master sheet must have columns: 한글 회사명, 영문 회사명, Industry.
Column names vary across events — re-map at the call site if your source uses
different headers.
"""
import pandas as pd
from korean_romanizer.romanizer import Romanizer
from thefuzz import fuzz, process


def romanize_korean(text):
    if not isinstance(text, str) or not text.strip():
        return ''
    return Romanizer(text).romanize().title()


def build_company_maps(df_companies, kr_col='한글 회사명', en_col='영문 회사명',
                      industry_col='Industry'):
    company_map = dict(zip(df_companies[kr_col], df_companies[en_col]))
    industry_map = dict(zip(df_companies[kr_col], df_companies[industry_col]))
    return company_map, industry_map


def resolve_company(kr_company, source_en_company, df_companies, company_map,
                    industry_map, infer_industry_fn,
                    kr_col='한글 회사명', fuzzy_threshold=80):
    """Return (english_company_name, industry).

    Args:
        kr_company: Korean company name from the source row.
        source_en_company: 영문회사명 from source row (may be NaN/None).
        df_companies: master DataFrame.
        company_map / industry_map: built via build_company_maps.
        infer_industry_fn: callable(text) -> Industry string. Used in step 4.
        kr_col: column name in df_companies holding Korean names.
        fuzzy_threshold: minimum thefuzz score to accept fuzzy match.
    """
    kr = str(kr_company or '').strip()
    if not kr:
        return romanize_korean(source_en_company) if source_en_company else '', None

    if kr in company_map:
        return company_map[kr], industry_map[kr]

    candidates = df_companies[kr_col].dropna().tolist()
    if candidates:
        match = process.extractOne(kr, candidates, scorer=fuzz.token_set_ratio)
        if match and match[1] >= fuzzy_threshold:
            return company_map[match[0]], industry_map[match[0]]

    if source_en_company and pd.notna(source_en_company):
        return str(source_en_company), infer_industry_fn(kr)
    return romanize_korean(kr), infer_industry_fn(kr)
