"""Certified metric: new, lost and retained customers. The definition lives in the .yaml card."""

import pandas as pd

from api.metrics.common import check_inputs, in_period, is_placeholder, load_card, refusal

CARD = load_card(__file__)
ONE_YEAR = pd.DateOffset(years=1)


def buyers(rows: pd.DataFrame, customer: str, amount: str) -> set:
    """Real customers with at least one positive amount in these rows."""
    bought = rows[(rows[amount] > 0) & ~rows[customer].map(is_placeholder)]
    return set(bought[customer])


def customer_retention(
    df: pd.DataFrame, roles: dict, start: str, end: str, store: str | None = None
) -> dict:
    refused = check_inputs(CARD, df, roles, store)
    if refused:
        return refused
    if store:
        df = df[df[roles["region"]] == store]

    first, last = pd.Timestamp(start), pd.Timestamp(end)
    if last >= first + ONE_YEAR:
        return refusal(CARD, "The period must be one year or shorter")
    previous_period = {
        "start": (first - ONE_YEAR).date().isoformat(),
        "end": (last - ONE_YEAR).date().isoformat(),
    }

    date, amount, customer = roles["date"], roles["amount"], roles["customer"]
    current = in_period(df, date, start, end)
    previous = in_period(df, date, previous_period["start"], previous_period["end"])
    now = buyers(current, customer, amount)
    before = buyers(previous, customer, amount)
    if not before:
        return refusal(
            CARD, "No customer bought in the comparison period", previous=previous_period
        )

    lost, new, retained = before - now, now - before, before & now
    lost_sales = previous[previous[customer].isin(lost)].groupby(customer)[amount].sum()
    # Largest first; equal sales in name order.
    top_lost = lost_sales.sort_index().sort_values(ascending=False, kind="stable").head(10)
    return {
        "status": "ok",
        "lost": len(lost),
        "new": len(new),
        "retained": len(retained),
        "customers_before": len(before),
        "customers_now": len(now),
        "lost_customers_sales_before": round(float(lost_sales.sum()), 2),
        "chart": {
            "type": "bar",
            "title": "Lost, new and retained customers",
            "x": {"label": "Customers", "values": ["Lost", "New", "Retained"]},
            "series": [{"name": "Customers", "values": [len(lost), len(new), len(retained)]}],
            "unit": "count",
        },
        "table": {
            "title": "Lost customers with the largest sales one year earlier",
            "columns": ["Customer", "Sales one year earlier"],
            "rows": [[str(name), round(float(value), 2)] for name, value in top_lost.items()],
        },
        "current": {"start": start, "end": end},
        "previous": previous_period,
        "metric": CARD["metric"],
    }
