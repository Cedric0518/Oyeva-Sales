"""Non-regression: the certified metrics must find the Atlas reference answers (answers.json)."""

import json
from pathlib import Path

import pandas as pd
import pytest

from api.metrics.sales_total import sales_total

ATLAS = Path(__file__).parent.parent / "evals" / "data" / "atlas"
ANSWERS = json.loads((ATLAS / "answers.json").read_text(encoding="utf-8"))
ROLES = {"date": "order_date", "amount": "amount"}


@pytest.fixture(scope="module")
def orders():
    return pd.read_csv(ATLAS / "atlas_orders.csv", parse_dates=["order_date"])


@pytest.mark.parametrize("year", ["2024", "2025", "2026"])
def test_sales_by_year(orders, year):
    result = sales_total(orders, ROLES, f"{year}-01-01", f"{year}-12-31")
    assert result["value"] == ANSWERS["sales_by_year"][year]
    assert result["value_without_duplicates"] == ANSWERS["sales_by_year_without_duplicates"][year]
