"""Resolve a Korean company name to (English Name, Industry).

The bundled master list `reference/company_mappings.xlsx` (sheet `CompanyMap`,
columns: `No.`, `한글 회사명`, `영문 회사명`, `Industry`) is ALWAYS the primary
lookup. An event-specific company sheet may be layered on top as a supplement,
but it never replaces the bundled mappings.

Resolution order (do not skip steps):
  1. Exact match against the mapping table (bundled first, then event extras).
  2. Normalized match — same table after stripping 주식회사 / (주) / punctuation
     / spacing / casing differences.
  3. Fuzzy match with `token_set_ratio >= fuzzy_threshold` (default 88).
  4. Nearest name — best candidate scoring `>= review_threshold` (default 65)
     is still adopted, because an unmatched 한글 회사명 should be converted to
     the most similar known English name rather than romanized. Flagged with
     `needs_review=True` so the converter can print it for a human check.
  5. Source row's own 영문회사명, when the nearest candidate is too weak.
  6. Romanize the Korean name; infer Industry from 회사명 + 부서 + 직책.

Set `review_threshold=0` to force step 4 for every unmatched name (never fall
through to romanization). Raise `fuzzy_threshold` when the event audience has
many short, easily-confused company names.

Public API:
    load_company_index(...)   -> CompanyIndex   # bundled xlsx (+ optional extras)
    CompanyIndex.resolve(...) -> CompanyMatch   # detailed, with score + method
    resolve_company(...)      -> (english, industry)   # legacy 2-tuple wrapper
"""
import os
import re
from typing import NamedTuple, Optional

import pandas as pd
from korean_romanizer.romanizer import Romanizer
from thefuzz import fuzz, process

# Bundled master list. Ships with the skill — do not edit per event.
DEFAULT_MAPPINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'company_mappings.xlsx')
DEFAULT_MAPPINGS_SHEET = 'CompanyMap'

DEFAULT_KR_COL = '한글 회사명'
DEFAULT_EN_COL = '영문 회사명'
DEFAULT_INDUSTRY_COL = 'Industry'

DEFAULT_FUZZY_THRESHOLD = 88
DEFAULT_REVIEW_THRESHOLD = 65

# Korean corporate-form tokens dropped before normalized comparison.
_KR_NOISE_TOKENS = ('주식회사', '유한회사', '(주)', '(유)', '(재)', '(사)', '㈜', '㈐')
# English corporate suffixes, matched on word boundaries so 'Incheon' survives.
_EN_SUFFIX_RE = re.compile(
    r'\b(co\.?,?\s*ltd\.?|co\.?|ltd\.?|inc\.?|corp\.?|corporation|company|limited)\b')
_PUNCT_RE = re.compile(r'[\s\-_.,·/&\'"()\[\]|]+')


class CompanyMatch(NamedTuple):
    """Outcome of one company-name resolution."""
    company: str            # English company name to write to Marketo
    industry: Optional[str]  # Industry from the mapping table, or None
    method: str             # exact | normalized | fuzzy | nearest | source_en | romanized | empty
    matched_kr: Optional[str]  # the 한글 회사명 row that was matched, if any
    score: Optional[int]    # fuzzy score for fuzzy/nearest, else None
    needs_review: bool      # True for low-confidence 'nearest' adoptions
    query: str = ''         # the 한글 회사명 that was looked up


def _clean(value):
    """Trim a cell value, treating NaN/None as empty string."""
    if value is None:
        return ''
    try:
        if pd.isna(value):
            return ''
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def romanize_korean(text):
    if not isinstance(text, str) or not text.strip():
        return ''
    return Romanizer(text).romanize().title()


def normalize_company(name):
    """Casefold and strip corporate forms / punctuation for loose matching.

    '(주)예시 전자' and '예시전자' both normalize to '예시전자'.
    """
    s = _clean(name).lower()
    if not s:
        return ''
    for token in _KR_NOISE_TOKENS:
        s = s.replace(token, '')
    s = _EN_SUFFIX_RE.sub('', s)
    return _PUNCT_RE.sub('', s)


class CompanyIndex:
    """Lookup table over 한글 회사명 → (영문 회사명, Industry).

    Holds the exact map, a normalized map, and the candidate list reused for
    every fuzzy lookup (built once — the bundled table has ~2.7k rows).
    """

    def __init__(self, company_map, industry_map=None,
                 fuzzy_threshold=DEFAULT_FUZZY_THRESHOLD,
                 review_threshold=DEFAULT_REVIEW_THRESHOLD):
        industry_map = industry_map or {}
        self.fuzzy_threshold = fuzzy_threshold
        self.review_threshold = review_threshold
        self.company_map = {}
        self.industry_map = {}
        self._normalized = {}
        for kr, en in company_map.items():
            kr_clean, en_clean = _clean(kr), _clean(en)
            if not kr_clean or not en_clean or kr_clean in self.company_map:
                continue  # first entry wins → bundled mappings beat event extras
            self.company_map[kr_clean] = en_clean
            industry = _clean(industry_map.get(kr))
            self.industry_map[kr_clean] = industry or None
            self._normalized.setdefault(normalize_company(kr_clean), kr_clean)
        self.candidates = list(self.company_map)

    def __len__(self):
        return len(self.company_map)

    @classmethod
    def from_dataframe(cls, df, kr_col=DEFAULT_KR_COL, en_col=DEFAULT_EN_COL,
                       industry_col=DEFAULT_INDUSTRY_COL, **kwargs):
        company_map, industry_map = build_company_maps(df, kr_col, en_col, industry_col)
        return cls(company_map, industry_map, **kwargs)

    def _hit(self, query, matched_kr, method, score=None, needs_review=False):
        return CompanyMatch(
            company=self.company_map[matched_kr],
            industry=self.industry_map.get(matched_kr),
            method=method,
            matched_kr=matched_kr,
            score=score,
            needs_review=needs_review,
            query=query,
        )

    def resolve(self, kr_company, source_en_company=None, infer_industry_fn=None):
        """Resolve one company name. See module docstring for the step order."""
        infer = infer_industry_fn or (lambda text: None)
        kr = _clean(kr_company)
        source_en = _clean(source_en_company)

        if not kr:
            if source_en:
                return CompanyMatch(source_en, None, 'source_en', None, None, False, kr)
            return CompanyMatch('', None, 'empty', None, None, False, kr)

        # 1. exact
        if kr in self.company_map:
            return self._hit(kr, kr, 'exact')

        # 2. normalized exact — spacing / (주) / punctuation differences only
        normalized = normalize_company(kr)
        if normalized and normalized in self._normalized:
            return self._hit(kr, self._normalized[normalized], 'normalized')

        # 3-4. fuzzy, then nearest-name adoption
        if self.candidates:
            match = process.extractOne(kr, self.candidates, scorer=fuzz.token_set_ratio)
            if match:
                best, score = match[0], int(match[1])
                if score >= self.fuzzy_threshold:
                    return self._hit(kr, best, 'fuzzy', score)
                if score >= self.review_threshold:
                    return self._hit(kr, best, 'nearest', score, needs_review=True)

        # 5. source row's own English name
        if source_en:
            return CompanyMatch(source_en, infer(kr), 'source_en', None, None, True, kr)

        # 6. romanize
        return CompanyMatch(romanize_korean(kr), infer(kr), 'romanized', None, None, True, kr)


def load_company_index(mappings_path=DEFAULT_MAPPINGS_PATH,
                       mappings_sheet=DEFAULT_MAPPINGS_SHEET,
                       extra_df=None, extra_kr_col=DEFAULT_KR_COL,
                       extra_en_col=DEFAULT_EN_COL,
                       extra_industry_col=DEFAULT_INDUSTRY_COL,
                       fuzzy_threshold=DEFAULT_FUZZY_THRESHOLD,
                       review_threshold=DEFAULT_REVIEW_THRESHOLD):
    """Build a CompanyIndex from the bundled mappings plus optional event extras.

    Args:
        mappings_path: bundled master list. Defaults to
            `reference/company_mappings.xlsx`.
        mappings_sheet: sheet name inside that file (`CompanyMap`).
        extra_df: optional event-specific company master (e.g. a `CompanyNames`
            sheet in the vendor export). Appended AFTER the bundled rows, so a
            한글 회사명 present in both resolves to the bundled English name.
        extra_*_col: column names inside `extra_df` when they differ.
    """
    company_map, industry_map = {}, {}
    if mappings_path:
        if not os.path.exists(mappings_path):
            raise FileNotFoundError(
                f'Company mappings file not found: {mappings_path}. '
                f'It ships with the skill under reference/.')
        df = pd.read_excel(mappings_path, sheet_name=mappings_sheet)
        company_map, industry_map = build_company_maps(
            df, DEFAULT_KR_COL, DEFAULT_EN_COL, DEFAULT_INDUSTRY_COL)

    if extra_df is not None and not extra_df.empty:
        extra_company, extra_industry = build_company_maps(
            extra_df, extra_kr_col, extra_en_col, extra_industry_col)
        for kr, en in extra_company.items():
            if kr not in company_map:
                company_map[kr] = en
                industry_map[kr] = extra_industry.get(kr)

    return CompanyIndex(company_map, industry_map,
                        fuzzy_threshold=fuzzy_threshold,
                        review_threshold=review_threshold)


def build_company_maps(df_companies, kr_col=DEFAULT_KR_COL, en_col=DEFAULT_EN_COL,
                       industry_col=DEFAULT_INDUSTRY_COL):
    """Return (company_map, industry_map) keyed by 한글 회사명."""
    company_map = dict(zip(df_companies[kr_col], df_companies[en_col]))
    industry_map = dict(zip(df_companies[kr_col], df_companies[industry_col]))
    return company_map, industry_map


# Single-entry cache so the legacy wrapper does not rebuild the index per row.
_index_cache = {}


def _cached_index(company_map, industry_map, fuzzy_threshold, review_threshold):
    key = (id(company_map), fuzzy_threshold, review_threshold)
    cached = _index_cache.get(key)
    if cached is not None and cached[0] is company_map:
        return cached[1]
    index = CompanyIndex(company_map, industry_map,
                         fuzzy_threshold=fuzzy_threshold,
                         review_threshold=review_threshold)
    _index_cache.clear()
    # Keep a strong ref to company_map so its id() stays valid while cached.
    _index_cache[key] = (company_map, index)
    return index


def resolve_company(kr_company, source_en_company, df_companies, company_map,
                    industry_map, infer_industry_fn,
                    kr_col=DEFAULT_KR_COL,
                    fuzzy_threshold=DEFAULT_FUZZY_THRESHOLD,
                    review_threshold=DEFAULT_REVIEW_THRESHOLD):
    """Legacy 2-tuple wrapper around CompanyIndex.resolve.

    Kept for converters that pass a single company master DataFrame. New
    converters should call `load_company_index(...)` and use
    `CompanyIndex.resolve(...)`, which also reports the match method and score.
    `df_companies` is unused — candidates come from `company_map`.
    """
    index = _cached_index(company_map, industry_map, fuzzy_threshold, review_threshold)
    match = index.resolve(kr_company, source_en_company, infer_industry_fn)
    return match.company, match.industry
