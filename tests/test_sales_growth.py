from pathlib import Path

import pandas as pd

from api.metrics.sales_growth import sales_growth

DATA = Path(__file__).parent / "data"
ROLES = {"date": "order_date", "amount": "amount", "region": "store"}


def small_growth():
    return pd.read_csv(DATA / "small_growth.csv", parse_dates=["order_date"])


def test_growth_takes_the_file_as_is():
    result = sales_growth(small_growth(), ROLES, "2026-01-01", "2026-03-31")
    assert result["previous"] == {
        "start": "2025-01-01",
        "end": "2025-03-31",
        "comparable_sales": 400.0,
    }
    assert result["current"]["comparable_sales"] == 610.0
    assert result["value"] == 0.525
    assert result["value_without_duplicates"] == 0.25
    assert result["months_left_out"] == []


def test_a_month_missing_in_one_year_is_left_out_of_both():
    result = sales_growth(small_growth(), ROLES, "2026-01-01", "2026-03-31", store="Online")
    assert result["months_left_out"] == ["2025-02"]
    assert result["value"] == -0.2
    assert result["value_all_months"] == 0.4


def test_refuses_when_no_month_has_sales_in_both_years():
    result = sales_growth(small_growth(), ROLES, "2026-01-01", "2026-01-31", store="Online")
    assert result["status"] == "refused"
    assert result["previous"] == {"start": "2025-01-01", "end": "2025-01-31"}


def test_refuses_a_period_longer_than_a_year():
    result = sales_growth(small_growth(), ROLES, "2025-01-01", "2026-03-31")
    assert result["status"] == "refused"
