from pathlib import Path

import pandas as pd

from api.metrics.average_basket import average_basket

DATA = Path(__file__).parent / "data"
ROLES = {"date": "order_date", "amount": "amount", "order_id": "order_id"}


def small_sales():
    return pd.read_csv(DATA / "small_sales.csv", parse_dates=["order_date"])


def test_an_order_made_only_of_returns_is_not_an_order():
    result = average_basket(small_sales(), ROLES, "2025-01-01", "2025-03-31")
    assert result["sales"] == 395.5
    assert result["orders"] == 4
    assert result["orders_with_only_returns"] == 1
    assert result["value"] == 98.88
    assert result["value_without_duplicates"] == 86.38


def test_refuses_without_an_order_column():
    roles = {"date": "order_date", "amount": "amount"}
    result = average_basket(small_sales(), roles, "2025-01-01", "2025-03-31")
    assert result["status"] == "refused"
    assert result["missing_roles"] == ["order_id"]
