from pathlib import Path

import pandas as pd

from api.metrics.sales_ranking import sales_ranking

DATA = Path(__file__).parent / "data"
ROLES = {"date": "order_date", "amount": "amount", "customer": "customer", "region": "store"}


def small_sales():
    return pd.read_csv(DATA / "small_sales.csv", parse_dates=["order_date"])


def test_walk_in_is_left_out_of_the_customer_ranking():
    result = sales_ranking(small_sales(), ROLES, "2025-01-01", "2025-12-31")
    assert result["chart"]["x"]["values"] == ["Gamma Ltd", "Beta Inc", "Alpha Co"]
    assert result["chart"]["series"][0]["values"] == [210.0, 175.25, 70.0]
    assert result["left_out"] == {"names": ["Walk-in"], "sales": 25.5, "share": 0.053}
    assert result["table"]["rows"][1] == ["Beta Inc", 175.25, 0.3645, 125.25]


def test_share_of_the_top_two():
    result = sales_ranking(small_sales(), ROLES, "2025-01-01", "2025-12-31", n=2)
    assert result["top_share"] == 0.8014


def test_products_are_ranked_too():
    df = pd.DataFrame(
        {
            "order_date": pd.to_datetime(["2025-01-05", "2025-01-06", "2025-01-07"]),
            "product": ["Pen", "Ink", "Pen"],
            "amount": [5.0, 12.0, 4.0],
        }
    )
    roles = {"date": "order_date", "amount": "amount", "product": "product"}
    result = sales_ranking(df, roles, "2025-01-01", "2025-12-31", by="product")
    assert result["chart"]["x"]["values"] == ["Ink", "Pen"]
    assert result["chart"]["series"][0]["values"] == [12.0, 9.0]


def test_refuses_without_a_customer_column():
    roles = {"date": "order_date", "amount": "amount"}
    result = sales_ranking(small_sales(), roles, "2025-01-01", "2025-12-31")
    assert result["status"] == "refused"
    assert result["missing_roles"] == ["customer"]
