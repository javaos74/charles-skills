"""Tests for name_splitter — covers Korean positional split, 2-char
surnames, English whitespace + CamelCase, and edge cases."""
import pytest

from name_splitter import (
    is_korean, split_english_name, split_korean_name, split_name,
)


@pytest.mark.parametrize('name, expected_first, expected_last', [
    ('김민수', '민수', '김'),       # 3-char standard
    ('이영희', '영희', '이'),       # 3-char standard
    ('박지', '지', '박'),           # 2-char (rare)
    ('남궁민지', '민지', '남궁'),   # 2-char surname, 4-char total
    ('황보영', '영', '황보'),       # 2-char surname, 3-char total
    ('제갈공명', '공명', '제갈'),
    ('선우진', '진', '선우'),
    ('김지훈호', '지훈호', '김'),   # 4-char with single-char surname
])
def test_split_korean_name(name, expected_first, expected_last):
    first, last = split_korean_name(name)
    assert (first, last) == (expected_first, expected_last)


@pytest.mark.parametrize('name, expected_first, expected_last', [
    ('John Doe', 'John', 'Doe'),
    ('John Michael Doe', 'John Michael', 'Doe'),
    ('Madonna', 'Madonna', ''),
    ('john doe', 'John', 'Doe'),
])
def test_split_english_name_with_spaces(name, expected_first, expected_last):
    first, last = split_english_name(name)
    assert (first, last) == (expected_first, expected_last)


def test_split_english_name_camelcase_korean_convention():
    # Korean CamelCase convention: LastFirst (e.g. KimMinsoo).
    # The splitter treats the FIRST CamelCase token as last name.
    first, last = split_english_name('KimMinsoo')
    assert (first, last) == ('Minsoo', 'Kim')


def test_split_name_dispatches_on_script():
    assert split_name('김민수') == ('민수', '김')
    assert split_name('John Doe') == ('John', 'Doe')


@pytest.mark.parametrize('value', ['', None, 123, '   '])
def test_split_name_handles_empty(value):
    first, last = split_name(value)
    assert first == '' and last == ''


@pytest.mark.parametrize('text, expected', [
    ('김민수', True),
    ('John Doe', False),
    ('김 Doe', True),       # mixed
    ('', False),
    (None, False),
    (123, False),
])
def test_is_korean(text, expected):
    assert is_korean(text) is expected
