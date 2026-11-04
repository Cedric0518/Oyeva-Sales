from pathlib import Path

import pandas as pd

from api.metrics.market_comparison import market_comparison

DATA = Path(__file__).parent / "data"
ROLES = {"date": "order_date", "amount": "amount", "region": "store"}


# A made-up benchmark, easy to compute by hand: core retail (retail trade minus cars minus fuel)
# is 600 a month in 2025, then 670, 650 and 720 in January, February and March 2026.
def series(year_2025: list, year_2026: list) -> dict:
    months = ["2025-01", "2025-02", "2025-03", "2026-01", "2026-02", "2026-03"]
    return dict(zip(months, year_2025 + year_2026, strict=True))


ONTARIO = {
    "retail_trade": series([1000.0] * 3, [1100.0, 1050.0, 1140.0]),
    "motor_vehicle_and_parts": series([300.0] * 3, [330.0, 300.0, 320.0]),
    "gasoline_stations": series([100.0] * 3, [100.0] * 3),
}
NO_FUEL = series([None] * 3, [None] * 3)
REFERENCE = {
    "table": "20-10-0056-01",
    "unit": "thousands of dollars",
    "published": "2026-03",
    "series": {"ON": ONTARIO, "NU": {**ONTARIO, "gasoline_stations": NO_FUEL}},
}


def small_growth():
    return pd.read_csv(DATA / "small_growth.csv", parse_dates=["order_date"])


def compare(start="2026-01-01", end="2026-03-31", province="ON", reference=REFERENCE, store=None):
    return market_comparison(small_growth(), ROLES, start, end, province, reference, store)


def test_gap_is_company_growth_minus_market_growth():
    result = compare()
    assert result["company_growth"] == 0.525
    assert result["market_growth"] == 0.1333
    assert result["value"] == 0.3917
    assert result["months_compared"] == ["2026-01", "2026-02", "2026-03"]
    assert result["benchmark"] == (
        "Ontario retail trade, excluding motor vehicle and parts dealers and gasoline stations"
    )
    assert result["source"] == "Statistics Canada, table 20-10-0056-01"
    assert result["published"] == "2026-03"


def test_months_not_yet_published_are_left_out_of_both():
    result = compare(reference={**REFERENCE, "published": "2026-02"})
    assert result["months_not_published"] == ["2026-03"]
    assert result["company_growth"] == 1.0
    assert result["market_growth"] == 0.1
    assert result["value"] == 0.9


def test_a_store_is_compared_on_its_own_months():
    result = compare(store="Online")
    assert result["months_compared"] == ["2026-03"]
    assert result["market_growth"] == 0.2
    assert result["value"] == -0.4


def test_refuses_when_the_benchmark_is_not_published():
    result = compare(province="NU")
    assert result["status"] == "refused"
    assert "Nunavut" in result["reason"]


def test_refuses_an_unknown_province():
    result = compare(province="XX")
    assert result["status"] == "refused"
    assert result["provinces"] == ["NU", "ON"]


def test_refuses_months_not_published_at_all():
    result = compare(start="2026-04-01", end="2026-06-30")
    assert result["status"] == "refused"
    assert result["published"] == "2026-03"


def test_passes_on_the_refusals_of_sales_growth():
    result = compare(start="2025-01-01", end="2026-03-31")
    assert result["status"] == "refused"
    assert result["metric"]["name"] == "market_comparison"
