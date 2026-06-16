"""Normalize phone numbers for the Marketo 'Phone number' column.

Marketo expects digits-only ('번호만 입력해야 함' per the template marker).
Two failure modes to handle:

1. Some vendor exports parse phones as int (e.g. 1097676948). The leading 0
   of Korean mobile numbers (01x) is lost. Restore it when the digit count
   matches a known Korean prefix.

2. Excel writes long all-digit strings in 'General' format, which Excel
   re-interprets as numbers on open — the leading 0 vanishes again.
   The fix is to write to a cell with number_format = '@' (Text). The
   `template_writer` applies '@' to every column listed in TEXT_COLUMNS.

Use:
    cleaned = normalize_phone(raw)
"""
import re


KOREAN_MOBILE_PREFIXES = ('10', '11', '16', '17', '18', '19')


def normalize_phone(value):
    if value is None:
        return ''
    if isinstance(value, float) and value != value:  # NaN
        return ''
    # int input lost its leading 0 already; convert via str
    digits = re.sub(r'\D', '', str(value))
    if not digits:
        return ''
    # Restore leading 0 for Korean mobile numbers exported as int
    if not digits.startswith('0') and digits.startswith(KOREAN_MOBILE_PREFIXES) and len(digits) in (10, 11):
        digits = '0' + digits
    return digits
