"""Write data rows into a Marketo Robot Import Lead Template without
disturbing the template's formatting.

The template uses pre-formatted blue header cells in row 1 and field
descriptions in rows 2-4. Data starts at row 5 (1-indexed). Always load
with openpyxl and save back to the new path so styles are preserved.

DO NOT use pandas.to_excel — it will strip the header formatting.
"""
import openpyxl
import pandas as pd


# 0-based template column indices for the standard Marketo template
# (Marketo Robot Import Lead Template_*.xlsx). Verify against your specific
# template revision; column indices may shift between template versions.
DEFAULT_COLUMN_MAP = {
    'Email Address': 0,
    'Company Name': 1,
    'First Name': 2,
    'Last Name': 3,
    'Country': 4,
    'State': 5,
    'SFDC Campaign ID': 6,
    'Import Channel': 7,
    'Import Name': 8,
    'Import Owner': 9,
    'Member Status': 10,
    'Channel Source': 11,
    'Channel': 12,
    'Channel Team': 15,
    'Channel Team Geo': 16,
    'Initial Response Date': 17,
    'Job title': 18,
    'Job Level': 19,
    'Department': 20,
    'Industry': 21,
    'Personal Contact Notes': 22,
    'Phone number': 23,
    'GDPR Opt-in': 24,
    'Requires Sales Follow-up': 26,
    'Company Name (Local)': 31,
}


def load_template_enums(template_file, sheet='Fields'):
    """Return (industries, job_levels, departments) lists from Fields sheet."""
    df_fields = pd.read_excel(template_file, sheet_name=sheet)
    return (
        df_fields['Industry'].dropna().tolist(),
        df_fields['Job Level'].dropna().tolist(),
        df_fields['Department'].dropna().tolist(),
    )


# Columns that must be written as Excel Text format (number_format = '@') so
# leading zeros and digit-only strings are preserved on open.
TEXT_COLUMNS = ('Phone number',)


def write_rows(template_file, output_file, rows, column_map=None,
               sheet_name='Sheet1', start_row=5, text_columns=TEXT_COLUMNS):
    """Write rows into a copy of the template, preserving styles.

    Args:
        template_file: path to template .xlsx
        output_file: path to write the populated copy
        rows: list[dict] keyed by Marketo column names from column_map
        column_map: dict[Marketo column name -> 0-based column index]
        sheet_name: target worksheet (default 'Sheet1')
        start_row: 1-based row where data begins (default 5; rows 1-4 = headers)
        text_columns: iterable of column names to force to Text format
            (number_format = '@'). Required for digit-only fields like
            phone numbers; otherwise Excel drops the leading 0 on open.
    """
    column_map = column_map or DEFAULT_COLUMN_MAP
    text_col_indices = {column_map[name] for name in text_columns if name in column_map}
    wb = openpyxl.load_workbook(template_file)
    ws = wb[sheet_name]
    for i, row in enumerate(rows):
        for col_name, col_idx in column_map.items():
            cell = ws.cell(row=start_row + i, column=col_idx + 1, value=row.get(col_name))
            if col_idx in text_col_indices:
                cell.number_format = '@'
    wb.save(output_file)
