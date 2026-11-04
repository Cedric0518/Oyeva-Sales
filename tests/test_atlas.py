"""Non-regression: the certified metrics must find the Atlas reference answers (answers.json)."""

import json
from pathlib import Path

import pandas as pd
import pytest

from api.metrics.customer_retention import customer_retention
from api.metrics.sales_by_period import sales_by_period
from api.metrics.sales_growth import sales_growth
from api.metrics.sales_ranking import sales_ranking
from api.metrics.sales_total import sales_total

ATLAS = Path(__file__).parent.parent / "evals" / "data" / "atlas"
ANSWERS = json.loads((ATLAS / "answers.json").read_text(encoding="utf-8"))
ROLES = {
    "date": "order_date",
    "amount": "amount",
    "region": "store",
    "customer": "customer",
    "product": "product",
}


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


def test_growth_jan_to_aug_2026(orders):
    result = sales_growth(orders, ROLES, "2026-01-01", "2026-08-31")
    assert result["value"] == ANSWERS["growth_jan_aug_2026_vs_2025"]
    assert result["months_left_out"] == []


def test_growth_for_all_of_2026_compares_the_same_months(orders):
    result = sales_growth(orders, ROLES, "2026-01-01", "2026-12-31")
    assert result["value"] == ANSWERS["growth_jan_aug_2026_vs_2025"]
    assert result["months_left_out"] == ["2026-09", "2026-10", "2026-11", "2026-12"]


@pytest.mark.parametrize("store", sorted(ANSWERS["growth_jan_aug_2026_vs_2025_by_store"]))
def test_growth_by_store_on_all_months(orders, store):
    result = sales_growth(orders, ROLES, "2026-01-01", "2026-08-31", store=store)
    assert result["value_all_months"] == ANSWERS["growth_jan_aug_2026_vs_2025_by_store"][store]


def test_online_growth_leaves_out_the_missing_july(orders):
    result = sales_growth(orders, ROLES, "2026-01-01", "2026-08-31", store="Online")
    assert result["months_left_out"] == ["2025-07"]
    assert result["value_all_months"] == 0.6906
    # July left out of both years; computed separately with pandas on atlas_orders.csv
    assert result["value"] == 0.4667


def test_top_10_customers_2025_without_walk_in(orders):
    result = sales_ranking(orders, ROLES, "2025-01-01", "2025-12-31")
    pairs = [[row[0], row[1]] for row in result["table"]["rows"]]
    assert pairs == ANSWERS["top10_customers_2025"]
    assert result["top_share"] == ANSWERS["top10_share_2025"]
    assert result["left_out"]["names"] == ["Walk-in"]
    assert result["left_out"]["share"] == ANSWERS["walk_in_share_2025"]


def test_top_10_products_2025(orders):
    result = sales_ranking(orders, ROLES, "2025-01-01", "2025-12-31", by="product")
    pairs = [[row[0], row[1]] for row in result["table"]["rows"]]
    assert pairs == ANSWERS["top10_products_2025"]


def test_customers_lost_new_and_retained_jan_to_aug(orders):
    result = customer_retention(orders, ROLES, "2026-01-01", "2026-08-31")
    counts = {key: result[key] for key in ("lost", "new", "retained")}
    assert counts == ANSWERS["customers_jan_aug_2025_vs_2026"]
    # Hamilton story: the school stopped buying after December 2025
    assert result["table"]["rows"][0][0] == "Bayfront Elementary School"
