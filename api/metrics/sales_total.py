"""Certified metric: total sales over a period. The definition lives in sales_total.yaml."""

import pandas as pd

from api.metrics.common import check_inputs, in_period, load_card

CARD = load_card(__file__)


def sales_total(
    df: pd.DataFrame, roles: dict, start: str, end: str, store: str | None = None
) -> dict:
    refused = check_inputs(CARD, df, roles, store)
    if refused:
        return refused
    if store:
        df = df[df[roles["region"]] == store]

    rows = in_period(df, roles["date"], start, end)
    amount = roles["amount"]
    return {
        "status": "ok",
        "value": round(float(rows[amount].sum()), 2),
        "value_without_duplicates": round(float(rows.drop_duplicates()[amount].sum()), 2),
        "rows": int(len(rows)),
        "period": {"start": start, "end": end},
        "store": store,  # None: the whole business
        "unit": "CAD",
        "metric": CARD["metric"],
    }
