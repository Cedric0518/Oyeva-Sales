from pathlib import Path

import pandas as pd

from api.metrics.customer_retention import customer_retention

DATA = Path(__file__).parent / "data"
ROLES = {"date": "order_date", "amount": "amount", "customer": "customer", "region": "store"}


def small_sales():
    return pd.read_csv(DATA / "small_sales.csv", parse_dates=["order_date"])


def test_lost_new_and_retained():
    result = customer_retention(small_sales(), ROLES, "2026-01-01", "2026-12-31")
    assert (result["lost"], result["new"], result["retained"]) == (2, 0, 1)
    assert result["table"]["rows"] == [["Gamma Ltd", 210.0], ["Beta Inc", 175.25]]
    assert result["chart"]["series"][0]["values"] == [2, 0, 1]


def test_a_customer_with_only_returns_did_not_buy():
    df = pd.DataFrame(
        {
            "order_date": pd.to_datetime(["2025-03-01", "2025-03-02", "2026-03-01", "2026-03-02"]),
            "customer": ["Echo", "Delta", "Echo", "Delta"],
            "amount": [10.0, -20.0, 10.0, 50.0],
        }
    )
    result = customer_retention(df, ROLES, "2026-01-01", "2026-12-31")
    assert (result["lost"], result["new"], result["retained"]) == (0, 1, 1)


def test_refuses_without_a_customer_column():
    roles = {"date": "order_date", "amount": "amount"}
    result = customer_retention(small_sales(), roles, "2026-01-01", "2026-12-31")
    assert result["status"] == "refused"
    assert result["missing_roles"] == ["customer"]
