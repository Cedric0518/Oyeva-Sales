"""Certified metric: sales by month, quarter or year. The definition lives in the .yaml card."""

import pandas as pd

from api.metrics.common import in_period, load_card, missing_roles, refusal

CARD = load_card(__file__)
# granularity: (pandas period code, axis label, chart type)
GRANULARITIES = {
    "month": ("M", "Month", "line"),
    "quarter": ("Q", "Quarter", "bar"),
    "year": ("Y", "Year", "bar"),
}


def rounded_or_none(sums: pd.Series, period) -> float | None:
    return round(float(sums[period]), 2) if period in sums.index else None


def sales_by_period(
    df: pd.DataFrame,
    roles: dict,
    start: str,
    end: str,
    granularity: str = "month",
    store: str | None = None,
) -> dict:
    needed = CARD["requires"] + (["region"] if store else [])
    missing = missing_roles(needed, roles)
    if missing:
        return refusal(
            CARD, "The file has no column for: " + ", ".join(missing), missing_roles=missing
        )
    if granularity not in GRANULARITIES:
        return refusal(
            CARD, f"Unknown granularity: {granularity}", granularities=list(GRANULARITIES)
        )
    if store:
        stores = sorted(df[roles["region"]].dropna().unique().tolist())
        if store not in stores:
            return refusal(CARD, f"Unknown store: {store}", stores=stores)

    rows = in_period(df, roles["date"], start, end)
    if rows.empty:
        return refusal(CARD, "The file has no rows in this period")

    code, label, chart_type = GRANULARITIES[granularity]
    periods = pd.to_datetime(rows[roles["date"]]).dt.to_period(code)
    axis = pd.period_range(periods.min(), periods.max(), freq=code)  # all stores
    if store:
        keep = rows[roles["region"]] == store
        rows, periods = rows[keep], periods[keep]

    amount = roles["amount"]
    sums = rows.groupby(periods)[amount].sum()
    unique = ~rows.duplicated()
    sums_unique = rows[unique].groupby(periods[unique])[amount].sum()

    x = [str(p) for p in axis]
    values = [rounded_or_none(sums, p) for p in axis]
    title = f"Sales by {granularity}" + (f", {store}" if store else "")
    return {
        "status": "ok",
        "chart": {
            "type": chart_type,
            "title": title,
            "x": {"label": label, "values": x},
            "series": [{"name": "Sales", "values": values}],
            "unit": "CAD",
        },
        "table": {
            "title": title,
            "columns": [label, "Sales", "Sales without duplicates"],
            "rows": [
                [x[i], values[i], rounded_or_none(sums_unique, p)] for i, p in enumerate(axis)
            ],
        },
        "period": {"start": start, "end": end},
        "unit": "CAD",
        "metric": CARD["metric"],
    }
