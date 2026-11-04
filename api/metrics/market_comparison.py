"""Certified metric: growth compared with provincial retail. The definition is in the .yaml card."""

import pandas as pd

from api.market.statcan import PROVINCES, core_retail
from api.metrics.common import load_card, refusal
from api.metrics.sales_growth import growth, sales_growth

CARD = load_card(__file__)


def market_comparison(
    df: pd.DataFrame,
    roles: dict,
    start: str,
    end: str,
    province: str,
    reference: dict,
    store: str | None = None,
) -> dict:
    """Compare with the province; reference is the Statistics Canada snapshot (statcan.py)."""
    if province not in reference["series"]:
        return refusal(CARD, f"Unknown province: {province}", provinces=sorted(reference["series"]))
    name = PROVINCES[province][0]
    published = pd.Period(reference["published"], freq="M")

    # Stop at the latest month Statistics Canada has published, and name the months after it.
    last_month = pd.Period(end, freq="M")
    not_published = [str(month) for month in pd.period_range(published + 1, last_month)]
    end = min(end, published.end_time.date().isoformat())
    if start > end:
        reason = "Statistics Canada has not published these months yet"
        return refusal(CARD, reason, published=str(published))

    company = sales_growth(df, roles, start, end, store)
    if company["status"] != "ok":
        return {**company, "metric": CARD["metric"]}

    months = company["months_compared"]
    year_before = {month: str(pd.Period(month, freq="M") - 12) for month in months}
    core = core_retail(reference, province)
    missing = sorted(m for m in months + list(year_before.values()) if core.get(m) is None)
    if missing:
        reason = f"Statistics Canada does not publish the benchmark of {name} for: "
        return refusal(CARD, reason + ", ".join(missing), published=str(published))

    now = sum(core[month] for month in months)
    before = sum(core[year_before[month]] for month in months)
    market = growth(now, before)
    gap = None
    if company["value"] is not None and market is not None:
        gap = round(company["value"] - market, 4)
    return {
        "status": "ok",
        "value": gap,
        "company_growth": company["value"],
        "company_growth_without_duplicates": company["value_without_duplicates"],
        "market_growth": market,
        "market_sales": {"current": now, "previous": before, "unit": reference["unit"]},
        "months_compared": months,
        "months_left_out": company["months_left_out"],
        "months_not_published": not_published,
        "benchmark": f"{name} retail trade, excluding motor vehicle and parts dealers and "
        "gasoline stations",
        "source": f"Statistics Canada, table {reference['table']}",
        "published": str(published),
        "metric": CARD["metric"],
    }
