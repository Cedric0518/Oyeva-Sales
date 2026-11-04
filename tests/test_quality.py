from pathlib import Path

import pandas as pd

from api.checks.quality import run_checks
from api.checks.roles import recognize_roles

DATA = Path(__file__).parent / "data"
TODAY = "2026-11-04"


def report(df: pd.DataFrame) -> dict:
    return {c["id"]: c for c in run_checks(df, recognize_roles(df), TODAY)}


def small_sales():
    return report(pd.read_csv(DATA / "small_sales.csv"))


def test_duplicates_returns_dates_and_placeholder():
    checks = small_sales()
    assert checks["duplicates"]["detail"] == "1 duplicate row"
    assert checks["duplicates"]["amount"] == 50.0
    assert checks["returns"]["detail"] == "1 return line"
    assert checks["returns"]["amount"] == -30.0
    assert checks["dates_out_of_range"]["detail"] == "1 row dated 2052"
    assert checks["placeholder_customer"]["status"] == "warning"
    assert checks["amount_mismatch"]["detail"] == "Not checked: no quantity or unit price column"


def test_a_store_month_without_rows():
    df = pd.DataFrame(
        {
            "date": ["2025-01-05", "2025-02-05", "2025-03-05", "2025-01-06", "2025-03-06"],
            "store": ["A", "A", "A", "B", "B"],
            "amount": [1.0, 1.0, 1.0, 1.0, 1.0],
        }
    )
    assert report(df)["missing_months"]["detail"] == "B: 2025-02"


def test_one_customer_written_three_ways():
    names = [
        "Lakeshore Dental Clinic",
        "LAKESHORE DENTAL CLINIC INC.",
        "Lakeshore Dental Clinic Inc",
    ]
    df = pd.DataFrame(
        {"date": ["2025-01-05"] * 4, "customer": [names[0], *names], "amount": [1.0] * 4}
    )
    detail = report(df)["name_variants"]["detail"]
    assert detail == "Lakeshore Dental Clinic appears in 3 spellings"


def test_quantity_times_price_against_amount():
    df = pd.DataFrame(
        {
            "date": ["2025-01-05", "2025-01-06"],
            "quantity": [2, 2],
            "unit_price": [3.49, 3.49],
            "amount": [6.98, 7.00],
        }
    )
    assert report(df)["amount_mismatch"]["detail"] == "1 row"


def test_no_amount_column_is_an_error():
    df = pd.DataFrame({"date": ["2025-01-05"], "customer": ["Alpha"]})
    assert report(df)["roles"]["status"] == "error"
