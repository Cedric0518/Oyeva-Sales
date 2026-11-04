import pandas as pd
from api.metrics.target_attainment import target_attainment

ROLES = {"date": "order_date", "amount": "amount", "region": "store", "target": "Targets.target"}


def orders():
    return pd.DataFrame(
        {
            "order_date": pd.to_datetime(["2025-01-10", "2025-02-10", "2025-01-12"]),
            "store": ["Main", "Main", "Online"],
            "amount": [80.0, 120.0, 50.0],
        }
    )


def targets():
    return pd.DataFrame(
        {
            "month": ["2025-01", "2025-02", "2025-01", "2025-02"],
            "store": ["Main", "Main", "Online", "Online"],
            "target": [100, 100, 50, 50],
        }
    )


def test_a_store_month_without_rows_is_left_out():
    result = target_attainment(orders(), ROLES, "2025-01-01", "2025-02-28", targets())
    assert result["left_out"] == ["Online 2025-02"]
    assert result["value"] == 1.0
    assert result["value_all_months"] == 0.8333
    assert result["table"]["rows"] == [
        ["2025-01", 130.0, 150.0, 0.8667],
        ["2025-02", 120.0, 100.0, 1.2],
    ]


def test_one_store():
    result = target_attainment(orders(), ROLES, "2025-01-01", "2025-02-28", targets(), "Online")
    assert result["value"] == 1.0
    assert result["value_all_months"] == 0.5
    assert result["chart"]["series"][0]["values"] == [50.0, None]


def test_refuses_without_targets():
    roles = {**ROLES, "target": None}
    result = target_attainment(orders(), roles, "2025-01-01", "2025-02-28", None)
    assert result["status"] == "refused"
    assert result["missing_roles"] == ["target"]
