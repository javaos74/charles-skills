"""Split full name into First Name / Last Name.

Marketo requires First Name + Last Name as separate fields. Source rosters
mix Korean (no space) and English (space-separated or CamelCase).

Usage:
    first, last = split_name(full_name)
"""
import re


TWO_CHAR_SURNAMES = [
    '남궁', '황보', '제갈', '사공', '선우', '서문', '독고', '어금', '망절',
]


def is_korean(text):
    if not isinstance(text, str):
        return False
    return bool(re.search('[가-힣]', text))


def split_korean_name(name):
    name = name.strip()
    if len(name) == 2:
        return name[1], name[0]
    if len(name) >= 3:
        if name[:2] in TWO_CHAR_SURNAMES:
            return name[2:], name[:2]
        return name[1:], name[0]
    return name, ''


def split_english_name(name):
    name = name.strip()
    if ' ' not in name:
        # CamelCase: "JohnDoe" -> ("Doe", "John")
        parts = re.findall('[A-Z][a-z]*', name)
        if len(parts) >= 2:
            return ' '.join(parts[1:]), parts[0]
        return name.title(), ''
    parts = name.split()
    if len(parts) == 1:
        return parts[0].title(), ''
    return ' '.join(p.title() for p in parts[:-1]), parts[-1].title()


def split_name(full_name):
    """Return (first_name, last_name) regardless of script."""
    if not isinstance(full_name, str) or not full_name.strip():
        return '', ''
    if is_korean(full_name):
        return split_korean_name(full_name)
    return split_english_name(full_name)
