"""Non-regression on Atlas: the comparison with Ontario retail, on a frozen Statistics Canada copy."""

import json
from pathlib import Path

import pandas as pd
import pytest

from api.metrics.market_comparison import market_comparison

ROOT = Path(__file__).parent.parent
ATLAS = ROOT / "evals" / "data" / "atlas"
ANSWERS = json.loads((ATLAS / "answers.json").read_text(encoding="utf-8"))
# Statistics Canada, table 20-10-0056-01, Ontario, release of 2026-10-23.
STATCAN_ON = json.loads((ROOT / "tests" / "data" / "statcan_on_2026-10-23.json").read_text())
ROLES = {"date": "order_date", "amount": "amount", "region": "store"}


@pytest.fixture(scope="module")
def orders():
    return pd.read_csv(ATLAS / "atlas_orders.csv", parse_dates=["order_date"])


def test_market_comparison_jan_to_aug_2026(orders):
    result = market_comparison(orders, ROLES, "2026-01-01", "2026-08-31", "ON", STATCAN_ON)
    assert result["company_growth"] == ANSWERS["growth_jan_aug_2026_vs_2025"]
    # Core retail of Ontario, January to August, in thousands of dollars.
    assert result["market_sales"]["current"] == 141245489.0
    assert result["market_sales"]["previous"] == 134959053.0
    assert result["market_growth"] == 0.0466
    assert result["value"] == 0.004
    assert result["published"] == "2026-08"
    chart = result["chart"]
    assert chart["x"]["values"] == result["months_compared"]
    assert [len(series["values"]) for series in chart["series"]] == [8, 8]
    assert chart["unit"] == "%"


def test_online_is_compared_with_the_market_without_july(orders):
    result = market_comparison(
        orders, ROLES, "2026-01-01", "2026-08-31", "ON", STATCAN_ON, store="Online"
    )
    assert "2026-07" not in result["months_compared"]
    assert result["months_left_out"] == ["2025-07"]
    assert result["company_growth"] == 0.4667
    assert result["market_growth"] == 0.0476
