"""Tests for phone_formatter — covers leading-0 restoration, NaN handling,
and Korean mobile prefix detection."""
import pytest

from phone_formatter import normalize_phone


@pytest.mark.parametrize('value, expected', [
    ('010-9767-6948', '01097676948'),
    (1097676948, '01097676948'),                # int export — leading 0 lost
    ('1097676948', '01097676948'),
    ('010 9767 6948', '01097676948'),
    ('010.9767.6948', '01097676948'),
])
def test_korean_mobile_restores_leading_zero(value, expected):
    assert normalize_phone(value) == expected


@pytest.mark.parametrize('value, expected', [
    ('02-1234-5678', '0212345678'),             # Seoul landline
    ('+82-10-1234-5678', '821012345678'),       # international keeps as-is
    ('9767676948', '9767676948'),               # 10 digits but no Korean prefix
])
def test_non_mobile_unchanged(value, expected):
    assert normalize_phone(value) == expected


@pytest.mark.parametrize('value', [None, '', 'abc', '---'])
def test_empty_or_garbage_returns_empty_string(value):
    assert normalize_phone(value) == ''


def test_nan_returns_empty_string():
    assert normalize_phone(float('nan')) == ''


@pytest.mark.parametrize('prefix', ['11', '16', '17', '18', '19'])
def test_legacy_prefixes_restored(prefix):
    # Legacy carrier prefixes (PCS, 016/017/018/019) — 10 digits stripped of 0.
    digits = prefix + '12345678'
    assert normalize_phone(digits) == '0' + digits
