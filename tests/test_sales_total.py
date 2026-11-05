from pathlib import Path

import pandas as pd

from api.metrics.sales_total import sales_total

DATA = Path(__file__).parent / "data"
ROLES = {"date": "order_date", "amount": "amount"}


def small_sales():
    return pd.read_csv(DATA / "small_sales.csv", parse_dates=["order_date"])


def test_sales_2025_takes_the_file_as_is():
    result = sales_total(small_sales(), ROLES, "2025-01-01", "2025-12-31")
    assert result["status"] == "ok"
    assert result["value"] == 480.75
    assert result["value_without_duplicates"] == 430.75
    assert result["rows"] == 8
    assert result["metric"]["name"] == "sales_total"


def test_a_time_on_the_last_day_still_counts():
    df = pd.DataFrame({"order_date": pd.to_datetime(["2025-12-31 18:45"]), "amount": [10.0]})
    result = sales_total(df, ROLES, "2025-01-01", "2025-12-31")
    assert result["value"] == 10.0


def test_refuses_without_an_amount_column():
    roles = {"date": "order_date", "amount": None}
    result = sales_total(small_sales(), roles, "2025-01-01", "2025-12-31")
    assert result["status"] == "refused"
    assert result["missing_roles"] == ["amount"]


def test_sales_of_one_store_and_the_result_says_which():
    roles = {**ROLES, "region": "store"}
    whole = sales_total(small_sales(), roles, "2025-01-01", "2025-12-31")
    online = sales_total(small_sales(), roles, "2025-01-01", "2025-12-31", store="Online")
    assert whole["store"] is None
    assert online["store"] == "Online"
    assert online["value"] == 180.0


def test_refuses_an_unknown_store_with_the_list_of_stores():
    roles = {**ROLES, "region": "store"}
    result = sales_total(small_sales(), roles, "2025-01-01", "2025-12-31", store="Queen Street")
    assert result["status"] == "refused"
    assert result["stores"] == ["Main", "Online"]
