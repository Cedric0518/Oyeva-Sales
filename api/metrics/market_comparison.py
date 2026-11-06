"""Certified metric: growth compared with provincial retail. The definition is in the .yaml card."""

import pandas as pd

from api.market.statcan import PROVINCES, core_retail
from api.metrics.common import in_period, load_card, refusal
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
    market_by_month = [growth(core[month], core[year_before[month]]) for month in months]
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
        "chart": chart(
            months,
            company_by_month(df, roles, company, store),
            market_by_month,
            f"{name} retail",
        ),
        "metric": CARD["metric"],
    }


def company_by_month(df: pd.DataFrame, roles: dict, company: dict, store: str | None) -> list:
    """The business's growth for each compared month, on the same rows as sales_growth."""
    if store:
        df = df[df[roles["region"]] == store]
    date, amount = roles["date"], roles["amount"]
    current = in_period(df, date, company["current"]["start"], company["current"]["end"])
    previous = in_period(df, date, company["previous"]["start"], company["previous"]["end"])
    now = current.groupby(pd.to_datetime(current[date]).dt.to_period("M"))[amount].sum()
    # The previous year moved forward by 12 months, to line up with the current one.
    before = previous.groupby(pd.to_datetime(previous[date]).dt.to_period("M") + 12)[amount].sum()
    months = [pd.Period(month, freq="M") for month in company["months_compared"]]
    return [growth(float(now.get(m, 0.0)), float(before.get(m, 0.0))) for m in months]


def percent(value: float | None) -> float | None:
    """A growth as a fraction (0.0506) becomes a percentage for the chart (5.06)."""
    return None if value is None else round(value * 100, 2)


def chart(months: list, company: list, market: list, market_name: str) -> dict:
    """Each month's growth against the same month one year earlier, the business and the market."""
    return {
        "type": "line",
        "title": "Growth against the same month one year earlier",
        "x": {"label": "Month", "values": months},
        "series": [
            {"name": "Your sales", "values": [percent(value) for value in company]},
            {"name": market_name, "values": [percent(value) for value in market]},
        ],
        "unit": "%",
    }
