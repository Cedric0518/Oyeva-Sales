"""Certified metric: average basket. The definition lives in the .yaml card."""

import pandas as pd

from api.metrics.common import check_inputs, in_period, load_card, refusal

CARD = load_card(__file__)


def average_basket(
    df: pd.DataFrame, roles: dict, start: str, end: str, store: str | None = None
) -> dict:
    refused = check_inputs(CARD, df, roles, store)
    if refused:
        return refused
    if store:
        df = df[df[roles["region"]] == store]

    rows = in_period(df, roles["date"], start, end)
    amount, order_id = roles["amount"], roles["order_id"]
    orders = rows.loc[rows[amount] > 0, order_id].nunique()
    if not orders:
        return refusal(CARD, "The file has no orders in this period")

    sales = rows[amount].sum()
    return {
        "status": "ok",
        "value": round(float(sales / orders), 2),
        "value_without_duplicates": round(float(rows.drop_duplicates()[amount].sum() / orders), 2),
        "sales": round(float(sales), 2),
        "orders": int(orders),
        "orders_with_only_returns": int(rows[order_id].nunique() - orders),
        "period": {"start": start, "end": end},
        "unit": "CAD",
        "metric": CARD["metric"],
    }
