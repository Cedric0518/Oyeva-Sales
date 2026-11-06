"""Read an uploaded sales file into what the certified functions need, and the upload response.

Real exports differ: CSV or Excel, comma or semicolon, decimal point or decimal comma, amounts
written "$1,234.50" or "1 234,50 $", title rows above the header, several sheets. Reading turns
text into a number or a date only when the whole column reads that way; everything else stays
text. Nothing is corrected: the checks report what is odd (docs/decisions/0010).
"""

import csv
import hashlib
import io
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePath

import pandas as pd

from api.checks.quality import EARLIEST, check, run_checks
from api.checks.roles import IDENTIFIER_ROLES, read_targets, recognize_roles
from api.market.statcan import PROVINCES
from api.tools import Dataset

FORMATS = {".csv": "csv", ".txt": "csv", ".xlsx": "excel", ".xlsm": "excel"}
DELIMITERS = [",", ";", "\t", "|"]
HEADER_SCAN = 15  # rows looked at to find the header row
PREVIEW_ROWS = 5
DATE_SHARE = 0.9  # share of values that must read as dates, as in roles.is_date
SESSION_FILE = "sales_data.csv"  # the name Code Interpreter sees
MAX_LISTED = 30  # stores named in the description of the file
DERIVED_AMOUNT = "amount (quantity x unit price)"  # added when the file has no amount column

# Cell text that means "no value" when a column is read as numbers or dates.
EMPTY = {"", "-", "--", "n/a", "na", "null", "none", "nan", "#n/a", "#value!"}
CURRENCY = re.compile(r"(?i)c\$|us\$|cad|usd|eur|[$€£]")
NUMBER = re.compile(r"[+-]?\d[\d.,]*")
SPACES = re.compile(r"[\s  ']")


class ReadError(Exception):
    """A file the API cannot read. code is one of the error codes of docs/contract.md."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class ReadFile:
    response: dict  # the body of POST /api/upload (docs/contract.md, section 5)
    data: Dataset  # what the certified functions run on
    csv: bytes  # the main sheet as read, given to Code Interpreter as SESSION_FILE
    description: str  # what the agent is told about the file


# ---------- raw cells: a list of rows per sheet ----------


def decode(content: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("latin-1")  # never fails: every byte is a character


def delimiter_of(text: str) -> str:
    """The delimiter that splits the first lines into the most fields, the same number per line."""
    lines = text.splitlines()[:50]
    best, best_score = ",", (0, 0)
    for delimiter in DELIMITERS:
        counts = [len(row) for row in csv.reader(lines, delimiter=delimiter) if any(row)]
        if not counts:
            continue
        fields, lines_with_it = Counter(counts).most_common(1)[0]
        score = (lines_with_it, fields) if fields > 1 else (0, 0)
        if score > best_score:
            best, best_score = delimiter, score
    return best


def csv_cells(content: bytes) -> tuple[dict[str, list[list]], str]:
    text = decode(content)
    delimiter = delimiter_of(text)
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    return {"": rows}, delimiter


def excel_cells(content: bytes) -> dict[str, list[list]]:
    sheets = pd.read_excel(
        io.BytesIO(content), sheet_name=None, header=None, dtype=object, engine="openpyxl"
    )
    return {name: df.where(df.notna(), None).values.tolist() for name, df in sheets.items()}


# ---------- one sheet: header, columns, types ----------


def blank(value) -> bool:
    return (
        value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == ""
    )


def header_row(rows: list[list]) -> int:
    """The first row with the most text cells: title rows above the header have fewer."""
    best, best_count = 0, -1
    for index, row in enumerate(rows[:HEADER_SCAN]):
        count = sum(isinstance(v, str) and not blank(v) for v in row)
        if count > best_count:
            best, best_count = index, count
    return best


def column_names(header: list) -> list[str]:
    names, seen = [], Counter()
    for position, value in enumerate(header, start=1):
        name = " ".join(str(value).split()) if not blank(value) else f"column_{position}"
        seen[name] += 1
        names.append(name if seen[name] == 1 else f"{name} ({seen[name]})")
    return names


def table(rows: list[list]) -> pd.DataFrame:
    """The rows under the header row, with empty rows and empty unnamed columns dropped."""
    if not rows:
        return pd.DataFrame()
    width = max(len(row) for row in rows)
    rows = [list(row) + [None] * (width - len(row)) for row in rows]
    top = header_row(rows)
    df = pd.DataFrame(rows[top + 1 :], columns=column_names(rows[top]), dtype=object)
    df = df.map(lambda v: None if blank(v) else (v.strip() if isinstance(v, str) else v))
    df = df.dropna(how="all")
    unnamed = [c for c in df.columns if c.startswith("column_") and df[c].isna().all()]
    return df.drop(columns=unnamed).reset_index(drop=True)


def decimal_mark(texts: list[str], hint: str) -> str:
    """The decimal mark of a column: the last mark when both appear, else the one followed by
    one, two or four or more digits; "1,234" alone is ambiguous and follows the hint."""
    both = [t for t in texts if "." in t and "," in t]
    if both:
        last = Counter("," if t.rfind(",") > t.rfind(".") else "." for t in both)
        return last.most_common(1)[0][0]
    for mark in (",", "."):
        if any(re.search(rf"\{mark}(\d{{1,2}}|\d{{4,}})$", t) for t in texts):
            return mark
    return hint


def as_numbers(column: pd.Series, hint: str) -> pd.Series | None:
    """The column as numbers if every value reads as one, else None. A leading zero (00123)
    marks a code, not a number."""
    values = column.dropna()
    if values.empty:
        return None
    if values.map(lambda v: isinstance(v, int | float) and not isinstance(v, bool)).all():
        return pd.to_numeric(column)
    texts = {}
    for index, value in values.items():
        text = str(value).strip()
        if text.lower() in EMPTY:
            continue
        text = SPACES.sub("", CURRENCY.sub("", text))
        negative = text.startswith("(") and text.endswith(")")  # (12.00): accounting negative
        text = text.strip("()")
        if text.endswith("-"):
            negative, text = True, text[:-1]
        if not NUMBER.fullmatch(text) or re.match(r"[+-]?0\d", text):
            return None
        texts[index] = (negative, text)
    if not texts:
        return None
    mark = decimal_mark([t for _, t in texts.values()], hint)
    other = "." if mark == "," else ","
    numbers = pd.Series(float("nan"), index=column.index)
    for index, (negative, text) in texts.items():
        try:
            number = float(text.replace(other, "").replace(mark, "."))
        except ValueError:
            return None
        numbers[index] = -number if negative else number
    if numbers.notna().all() and (numbers == numbers.round()).all():
        return numbers.astype("int64")
    return numbers  # floats: a missing value stays NaN, never a zero


def day_first(texts: pd.Series) -> bool | None:
    """True for 13/02/2025, False for 02/13/2025, None when every date reads both ways."""
    parts = texts.str.extract(r"^\s*(\d{1,2})[/.-](\d{1,2})[/.-]\d{2,4}")
    parts = parts.dropna().astype(int)
    if parts.empty:
        return False
    if (parts[0] > 12).any():
        return True
    if (parts[1] > 12).any():
        return False
    return None


def as_dates(column: pd.Series) -> tuple[pd.Series | None, dict]:
    """The column as dates if at least 90% of the values read as dates, else None, with notes:
    values that did not read, and whether day and month could be told apart."""
    values = column.dropna()
    if values.empty or pd.api.types.is_numeric_dtype(column):
        return None, {}
    if values.map(lambda v: isinstance(v, datetime)).all():
        return pd.to_datetime(column), {}
    texts = values.map(lambda v: v.isoformat() if isinstance(v, datetime) else str(v))
    if texts.map(lambda t: bool(re.search(r"\d", t)) and len(t) >= 6).mean() < DATE_SHARE:
        return None, {}  # month names ("March") and short codes are not dates
    first = day_first(texts)
    sample = pd.to_datetime(texts.head(200), format="mixed", dayfirst=bool(first), errors="coerce")
    if sample.notna().mean() < DATE_SHARE:
        return None, {}
    dates = pd.to_datetime(texts, format="mixed", dayfirst=bool(first), errors="coerce")
    if dates.notna().mean() < DATE_SHARE:
        return None, {}
    notes = {"unreadable": int(dates.isna().sum()), "ambiguous": first is None}
    return dates.reindex(column.index), notes


def typed(df: pd.DataFrame, hint: str) -> tuple[pd.DataFrame, dict]:
    """Numbers and dates where a whole column reads that way; notes on the date columns."""
    notes = {}
    for name in df.columns:
        numbers = as_numbers(df[name], hint)
        if numbers is not None:
            df[name] = numbers
            continue
        dates, date_notes = as_dates(df[name])
        if dates is not None:
            df[name] = dates
            notes[name] = date_notes
    return df, notes


def column_type(column: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(column):
        return "date"
    if pd.api.types.is_numeric_dtype(column) and not pd.api.types.is_bool_dtype(column):
        return "number"
    return "text"


# ---------- the whole file ----------


def main_sheet(sheets: dict[str, pd.DataFrame]) -> str:
    """The sheet with a date and an amount column and the most rows, else the biggest sheet."""
    ranked = sorted(sheets, key=lambda name: len(sheets[name]), reverse=True)
    for name in ranked:
        roles = recognize_roles(sheets[name])
        if roles["date"] and (roles["amount"] or (roles["quantity"] and roles["unit_price"])):
            return name
    return ranked[0]


def json_value(value):
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat() if value == value.normalize() else value.isoformat()
    if hasattr(value, "item"):  # numpy number
        return value.item()
    return value


def preview(df: pd.DataFrame) -> dict:
    rows = df.head(PREVIEW_ROWS).astype(object).values.tolist()
    return {"columns": list(df.columns), "rows": [[json_value(v) for v in row] for row in rows]}


def identifier_text(value) -> str | None:
    if pd.isna(value):
        return None
    return str(int(value)) if float(value).is_integer() else str(value)


def settle_types(df: pd.DataFrame, roles: dict, notes: dict) -> None:
    """Identifiers written as numbers become text (customer 13085, not 13085.0), and a column
    found as the date by its name but not read as dates loses the role, so that the certified
    functions refuse instead of failing."""
    for role in IDENTIFIER_ROLES:
        column = roles.get(role)
        if column and pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].map(identifier_text).astype(object)
    date = roles.get("date")
    if date and not pd.api.types.is_datetime64_any_dtype(df[date]):
        dates, date_notes = as_dates(df[date])
        if dates is None:
            roles["date"] = None
        else:
            df[date], notes[date] = dates, date_notes


def derive_amount(df: pd.DataFrame, roles: dict) -> dict | None:
    """With no amount column, the amount is quantity x unit price, in a column that says so.
    It is a definition shown to the user, not a correction: the check reports it."""
    quantity, price = roles.get("quantity"), roles.get("unit_price")
    if roles.get("amount") or not quantity or not price:
        return None
    df[DERIVED_AMOUNT] = (df[quantity] * df[price]).round(2)
    roles["amount"] = DERIVED_AMOUNT
    detail = f"No amount column: amount computed as {quantity} x {price}"
    return check("derived_amount", "Amount computed", "warning", detail)


def reading_checks(notes: dict, roles: dict) -> list[dict]:
    """Two more checks when the date column needed a choice: values that did not read as dates,
    and dates such as 03/04/2025 that read both ways."""
    date = roles.get("date")
    if not date or date not in notes:
        return []
    found = []
    count = notes[date].get("unreadable", 0)
    if count:
        detail = f"{count} row{'s' if count > 1 else ''} with a {date} that is not a date"
        found.append(check("unreadable_dates", "Values that are not dates", "warning", detail))
    if notes[date].get("ambiguous"):
        detail = f"Dates such as 03/04 in {date} were read as month/day"
        found.append(check("ambiguous_dates", "Day and month order", "warning", detail))
    return found


def clean(text, limit: int = 60) -> str:
    """A name from the file, safe to put in the agent's instructions: one line, no braces."""
    return re.sub(r"[{}\s]+", " ", str(text)).strip()[:limit]


def describe(
    file_name: str,
    sheet: str,
    df: pd.DataFrame,
    roles: dict,
    region: str,
    today: pd.Timestamp,
    checks: list[dict],
) -> str:
    """What the agent is told about the session file (structured input "dataset"): the agent
    never sees the upload report otherwise, so the checks with a warning are listed too."""
    where = f", sheet {clean(sheet)}" if sheet else ""
    lines = [f"- File: {clean(file_name, 100)}{where}, {len(df):,} rows."]
    if roles.get("date"):
        dates = pd.to_datetime(df[roles["date"]], errors="coerce")
        dates = dates[(dates >= EARLIEST) & (dates <= today)]
        if not dates.empty:
            first, last = dates.min().date(), dates.max().date()
            lines.append(f"- Dates from {first} to {last}.")
    found = [f"{role} = {clean(column)}" for role, column in roles.items() if column]
    lines.append("- Columns the certified functions use: " + "; ".join(found) + ".")
    missing = [role for role in ("date", "amount") if not roles.get(role)]
    if missing:
        lines.append(f"- No {' or '.join(missing)} column: the certified functions refuse.")
    used = {column for column in roles.values() if column}
    others = [clean(c) for c in df.columns if c not in used]
    if others:
        lines.append("- Other columns: " + ", ".join(others) + ".")
    if roles.get("region"):
        stores = sorted(str(s) for s in df[roles["region"]].dropna().unique())
        named = ", ".join(clean(s) for s in stores[:MAX_LISTED])
        more = f", and {len(stores) - MAX_LISTED} more" if len(stores) > MAX_LISTED else ""
        lines.append(f"- Stores (column {clean(roles['region'])}): {named}{more}.")
    lines.append(f"- Province: {PROVINCES[region][0]} ({region}).")
    warnings = [c for c in checks if c["status"] != "ok"]
    if warnings:
        lines.append("- Checks with a warning:")
        lines += [f"  - {c['name']}: {clean(c['detail'], 200)}." for c in warnings]
    lines.append(
        f"- In Code Interpreter the same rows are in the file whose name ends with "
        f"{SESSION_FILE}, read the same way as the certified functions read them."
    )
    return "\n".join(lines)


def session_csv(df: pd.DataFrame) -> bytes:
    dates = [df[c] for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    with_time = any((d.dropna() != d.dropna().dt.normalize()).any() for d in dates)
    date_format = "%Y-%m-%d %H:%M:%S" if with_time else "%Y-%m-%d"
    return df.to_csv(index=False, date_format=date_format).encode("utf-8")


def read_sales_file(
    content: bytes,
    file_name: str,
    region: str,
    reference: dict | None = None,
    today: str | None = None,
) -> ReadFile:
    """Read an uploaded sales file. Raises ReadError for a format or a file the API cannot read."""
    kind = FORMATS.get(PurePath(file_name).suffix.lower())
    if kind is None:
        raise ReadError("unsupported_format", "The sales file must be a CSV or Excel (.xlsx) file.")
    try:
        if kind == "csv":
            cells, delimiter = csv_cells(content)
            hint = "," if delimiter == ";" else "."
        else:
            cells, hint = excel_cells(content), "."
    except Exception as error:  # a corrupt or mislabeled file, whatever the library raises
        raise ReadError(
            "unreadable_file", "The file could not be read. Is it a valid sales file?"
        ) from error

    sheets, notes = {}, {}
    for name, rows in cells.items():
        df, sheet_notes = typed(table(rows), hint)
        if not df.empty and len(df.columns) > 1:
            sheets[name], notes[name] = df, sheet_notes
    if not sheets:
        raise ReadError("unreadable_file", "The file has no table with a header and rows.")

    main = main_sheet(sheets)
    df = sheets[main]
    others = {name: sheet for name, sheet in sheets.items() if name != main}
    roles = recognize_roles(df, others)
    settle_types(df, roles, notes[main])
    derived = derive_amount(df, roles)
    day = pd.Timestamp(today) if today else pd.Timestamp.today().normalize()
    checks = run_checks(df, roles, day.date().isoformat()) + reading_checks(notes[main], roles)
    if derived:
        checks.insert(1, derived)

    response = {
        "dataset_id": "ds_" + hashlib.sha256(content).hexdigest()[:16],
        "file_name": file_name,
        "sheets": list(cells) if kind == "excel" else [],
        "rows": len(df),
        "columns": [{"name": c, "type": column_type(df[c])} for c in df.columns],
        "roles": roles,
        "preview": preview(df),
        "checks": checks,
        "region": region,
        "context": None,
    }
    data = Dataset(df, roles, read_targets(others, roles), region, reference)
    sheet = main if kind == "excel" else ""
    description = describe(file_name, sheet, df, roles, region, day, checks)
    return ReadFile(response, data, session_csv(df), description)
