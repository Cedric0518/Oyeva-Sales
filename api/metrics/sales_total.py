"""Certified metric: total sales over a period. The definition lives in sales_total.yaml."""

import pandas as pd

from api.metrics.common import in_period, load_card, missing_roles, refusal

CARD = load_card(__file__)


def sales_total(df: pd.DataFrame, roles: dict, start: str, end: str) -> dict:
    missing = missing_roles(CARD["requires"], roles)
    if missing:
        return refusal(
            CARD, "The file has no column for: " + ", ".join(missing), missing_roles=missing
        )

    rows = in_period(df, roles["date"], start, end)
    amount = roles["amount"]
    return {
        "status": "ok",
        "value": round(float(rows[amount].sum()), 2),
        "value_without_duplicates": round(float(rows.drop_duplicates()[amount].sum()), 2),
        "rows": int(len(rows)),
        "period": {"start": start, "end": end},
        "unit": "CAD",
        "metric": CARD["metric"],
    }
