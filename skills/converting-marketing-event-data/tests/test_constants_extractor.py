"""End-to-end test for constants_extractor against generated samples."""
import os
import subprocess
import sys

import pytest

from constants_extractor import (
    build_event_constants, detect_constant_columns, extract_first_row_values,
)


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(REPO_ROOT, 'examples')
TEMPLATE = os.path.join(EXAMPLES_DIR, 'sample_template.xlsx')
PRIOR = os.path.join(EXAMPLES_DIR, 'sample_prior_result.xlsx')


@pytest.fixture(scope='module', autouse=True)
def ensure_samples():
    if not os.path.exists(PRIOR):
        subprocess.run(
            [sys.executable, os.path.join(EXAMPLES_DIR, 'generate_samples.py')],
            check=True,
        )


def test_detect_constant_columns_finds_marker_columns():
    cols = detect_constant_columns(TEMPLATE)
    headers = {h for _, h, _ in cols}
    # Required 고정값 columns from the template marker.
    assert 'Country' in headers
    assert 'Import Owner' in headers
    assert 'Import Name' in headers
    assert 'SFDC Campaign ID' in headers
    assert 'Channel Team' in headers
    assert 'Channel Team Geo' in headers
    assert 'Initial Response Date' in headers


def test_extracted_values_match_sample_row():
    values = build_event_constants(TEMPLATE, PRIOR)
    assert values['Country'] == 'Korea, Republic of'
    assert values['Import Owner'] == 'owner@example.com'
    assert values['Channel Team'] == 'Field Marketing'
    assert values['Channel Team Geo'] == 'APJ'
    assert values['GDPR Opt-in'] == 'Yes'


def test_skips_blank_cells():
    # The blank template (no row 5) should produce no extracted values.
    values = extract_first_row_values(TEMPLATE, detect_constant_columns(TEMPLATE))
    assert values == {}
