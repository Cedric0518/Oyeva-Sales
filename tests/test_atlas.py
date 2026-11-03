"""Non-regression: the certified metrics must find the Atlas reference answers (answers.json)."""

import json
from pathlib import Path

import pandas as pd
import pytest

from api.metrics.sales_by_period import sales_by_period
from api.metrics.sales_total import sales_total

ATLAS = Path(__file__).parent.parent / "evals" / "data" / "atlas"
ANSWERS = json.loads((ATLAS / "answers.json").read_text(encoding="utf-8"))
ROLES = {"date": "order_date", "amount": "amount", "region": "store"}


@pytest.fixture(scope="module")
def orders():
    return pd.read_csv(ATLAS / "atlas_orders.csv", parse_dates=["order_date"])


@pytest.mark.parametrize("year", ["2024", "2025", "2026"])
def test_sales_by_year(orders, year):
    result = sales_total(orders, ROLES, f"{year}-01-01", f"{year}-12-31")
    assert result["value"] == ANSWERS["sales_by_year"][year]
    assert result["value_without_duplicates"] == ANSWERS["sales_by_year_without_duplicates"][year]


def test_sales_by_month(orders):
    result = sales_by_period(orders, ROLES, "2024-01-01", "2026-12-31")
    chart = result["chart"]
    by_month = dict(zip(chart["x"]["values"], chart["series"][0]["values"], strict=True))
    assert by_month == ANSWERS["sales_by_month"]


def test_queen_street_closed_in_march_2025(orders):
    result = sales_by_period(
        orders, ROLES, "2025-01-01", "2025-12-31", store="Toronto - Queen Street"
    )
    values = result["chart"]["series"][0]["values"]
    assert values[1] == ANSWERS["story"]["queen_street_feb_2025"]
    assert values[2] == ANSWERS["story"]["queen_street_mar_2025"]


def test_online_july_2025_is_a_gap(orders):
    result = sales_by_period(orders, ROLES, "2025-01-01", "2025-12-31", store="Online")
    assert result["chart"]["series"][0]["values"][6] is None
    assert "Online 2025-07" in ANSWERS["checks"]["months_without_sales"]
