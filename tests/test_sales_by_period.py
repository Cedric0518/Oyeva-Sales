from pathlib import Path

import pandas as pd

from api.metrics.sales_by_period import sales_by_period

DATA = Path(__file__).parent / "data"
ROLES = {"date": "order_date", "amount": "amount", "region": "store"}


def small_sales():
    return pd.read_csv(DATA / "small_sales.csv", parse_dates=["order_date"])


def test_months_without_rows_are_null_not_zero():
    result = sales_by_period(small_sales(), ROLES, "2025-01-01", "2025-12-31")
    chart = result["chart"]
    assert chart["x"]["values"][0] == "2025-01"
    assert chart["x"]["values"][-1] == "2025-12"
    expected = [200.0, 25.5, 170.0, None, None, 75.25, None, None, None, None, None, 10.0]
    assert chart["series"][0]["values"] == expected
    assert result["table"]["rows"][0] == ["2025-01", 200.0, 150.0]


def test_a_store_with_no_row_in_a_month_gets_null():
    result = sales_by_period(small_sales(), ROLES, "2025-01-01", "2025-12-31", store="Online")
    values = result["chart"]["series"][0]["values"]
    assert values[0] is None
    assert values[2] == 170.0
    assert values[11] == 10.0


def test_quarters():
    result = sales_by_period(small_sales(), ROLES, "2025-01-01", "2025-12-31", "quarter")
    assert result["chart"]["x"]["values"] == ["2025Q1", "2025Q2", "2025Q3", "2025Q4"]
    assert result["chart"]["series"][0]["values"] == [395.5, 75.25, None, 10.0]


def test_refuses_an_unknown_store_and_lists_the_real_ones():
    result = sales_by_period(small_sales(), ROLES, "2025-01-01", "2025-12-31", store="Downtown")
    assert result["status"] == "refused"
    assert result["stores"] == ["Main", "Online"]
