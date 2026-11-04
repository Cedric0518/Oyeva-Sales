"""The data report: eight checks run on the file as uploaded. Nothing is corrected, only reported.

Each check follows docs/contract.md: id, name, status (ok, warning, error), detail, amount.
"""

import re

import pandas as pd

from api.metrics.common import is_placeholder

EARLIEST = pd.Timestamp("1990-01-01")
# Legal-form words dropped when comparing customer names ("Lakeshore Dental Clinic Inc.").
SUFFIXES = {"inc", "incorporated", "corp", "corporation", "ltd", "limited", "llc", "co", "company"}


def check(id_: str, name: str, status: str, detail: str, amount: float | None = None) -> dict:
    return {"id": id_, "name": name, "status": status, "detail": detail, "amount": amount}


def plural(count: int, word: str) -> str:
    return f"{count} {word}" + ("" if count == 1 else "s")


def roles_check(roles: dict) -> dict:
    name = "Column roles"
    missing = [role for role in ("date", "amount") if not roles.get(role)]
    if missing:
        detail = f"No {' or '.join(missing)} column found: certified metrics cannot run"
        return check("roles", name, "error", detail)
    words = {"date": "Date", "amount": "amount", "customer": "customer", "order_id": "order"}
    found = [word for role, word in words.items() if roles.get(role)]
    listed = ", ".join(found[:-1]) + " and " + found[-1]
    return check("roles", name, "ok", f"{listed} columns identified")


def duplicates_check(df: pd.DataFrame, roles: dict) -> dict:
    copies = df[df.duplicated()]
    name = "Duplicate rows"
    if copies.empty:
        return check("duplicates", name, "ok", "No duplicate rows")
    amount = round(float(copies[roles["amount"]].sum()), 2) if roles.get("amount") else None
    return check("duplicates", name, "warning", plural(len(copies), "duplicate row"), amount)


def amount_mismatch_check(df: pd.DataFrame, roles: dict) -> dict:
    name = "Quantity x unit price differs from amount"
    columns = [roles.get(role) for role in ("quantity", "unit_price", "amount")]
    if not all(columns):
        return check("amount_mismatch", name, "ok", "Not checked: no quantity or unit price column")
    quantity, price, amount = (df[column] for column in columns)
    differs = ((quantity * price).round(2) - amount).abs() > 0.01
    if not differs.any():
        return check("amount_mismatch", name, "ok", "Every row matches")
    return check("amount_mismatch", name, "warning", plural(int(differs.sum()), "row"))


def name_key(name) -> str:
    words = re.sub(r"[^a-z0-9 ]", " ", str(name).lower()).split()
    while words and words[-1] in SUFFIXES:
        words.pop()
    return " ".join(words)


def name_variants_check(df: pd.DataFrame, roles: dict) -> dict:
    name = "Same customer written several ways"
    if not roles.get("customer"):
        return check("name_variants", name, "ok", "Not checked: no customer column")
    names = df[roles["customer"]][~df[roles["customer"]].map(is_placeholder)]
    counts = names.value_counts()
    groups = counts.groupby(counts.index.map(name_key))
    found = []
    for _, spellings in groups:
        if len(spellings) > 1:
            most_used = spellings.sort_values(ascending=False).index[0]
            found.append(f"{most_used} appears in {len(spellings)} spellings")
    if not found:
        return check("name_variants", name, "ok", "No customer written several ways")
    return check("name_variants", name, "warning", "; ".join(sorted(found)))


def valid_dates(df: pd.DataFrame, roles: dict, today: pd.Timestamp) -> pd.Series:
    dates = pd.to_datetime(df[roles["date"]], errors="coerce")
    return dates.where((dates >= EARLIEST) & (dates <= today))


def missing_months_check(df: pd.DataFrame, roles: dict, today: pd.Timestamp) -> dict:
    name = "Months without sales"
    if not roles.get("date"):
        return check("missing_months", name, "ok", "Not checked: no date column")
    months = valid_dates(df, roles, today).dt.to_period("M")
    if months.isna().all():
        return check("missing_months", name, "ok", "Not checked: no valid date")
    calendar = pd.period_range(months.min(), months.max(), freq="M")
    stores = df[roles["region"]] if roles.get("region") else pd.Series("All", index=df.index)
    gaps = []
    for store in sorted(stores.dropna().unique()):
        present = set(months[stores == store].dropna())
        absent = [str(m) for m in calendar if m not in present]
        if absent:
            gaps.append(f"{store}: {', '.join(absent)}")
    if not gaps:
        return check("missing_months", name, "ok", "Every month has sales")
    return check("missing_months", name, "warning", "; ".join(gaps))


def dates_out_of_range_check(df: pd.DataFrame, roles: dict, today: pd.Timestamp) -> dict:
    name = "Dates outside the period"
    if not roles.get("date"):
        return check("dates_out_of_range", name, "ok", "Not checked: no date column")
    dates = pd.to_datetime(df[roles["date"]], errors="coerce")
    outside = dates[(dates < EARLIEST) | (dates > today)]
    if outside.empty:
        return check("dates_out_of_range", name, "ok", "Every date is between 1990 and today")
    years = ", ".join(str(year) for year in sorted(outside.dt.year.unique()))
    return check(
        "dates_out_of_range", name, "warning", f"{plural(len(outside), 'row')} dated {years}"
    )


def placeholder_check(df: pd.DataFrame, roles: dict) -> dict:
    name = "Placeholder customer"
    if not roles.get("customer"):
        return check("placeholder_customer", name, "ok", "Not checked: no customer column")
    names = df[roles["customer"]].dropna().unique()
    found = sorted(str(n) for n in names if is_placeholder(n))
    if not found:
        return check("placeholder_customer", name, "ok", "Every customer name is a real customer")
    quoted = ", ".join(f'"{n}"' for n in found)
    verb = "is not a single customer" if len(found) == 1 else "are not single customers"
    detail = f"{quoted} {verb}; excluded from customer metrics"
    return check("placeholder_customer", name, "warning", detail)


def returns_check(df: pd.DataFrame, roles: dict) -> dict:
    name = "Returns"
    if not roles.get("amount"):
        return check("returns", name, "ok", "Not checked: no amount column")
    negative = df[roles["amount"]][df[roles["amount"]] < 0]
    if negative.empty:
        return check("returns", name, "ok", "No return lines")
    detail = plural(len(negative), "return line")
    return check("returns", name, "ok", detail, round(float(negative.sum()), 2))


def run_checks(df: pd.DataFrame, roles: dict, today: str | None = None) -> list[dict]:
    """The eight checks of the data report, in the order of the contract."""
    today = pd.Timestamp(today) if today else pd.Timestamp.today().normalize()
    return [
        roles_check(roles),
        duplicates_check(df, roles),
        amount_mismatch_check(df, roles),
        name_variants_check(df, roles),
        missing_months_check(df, roles, today),
        dates_out_of_range_check(df, roles, today),
        placeholder_check(df, roles),
        returns_check(df, roles),
    ]
