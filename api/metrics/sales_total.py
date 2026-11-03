"""Certified metric: total sales over a period. The definition lives in sales_total.yaml."""

from pathlib import Path

import pandas as pd
import yaml

CARD = yaml.safe_load(Path(__file__).with_suffix(".yaml").read_text(encoding="utf-8"))
METRIC = {"name": CARD["name"], "version": CARD["version"], "definition": CARD["definition"]}


def sales_total(df: pd.DataFrame, roles: dict, start: str, end: str) -> dict:
    missing = [role for role in CARD["requires"] if not roles.get(role)]
    if missing:
        return {
            "status": "refused",
            "reason": "The file has no column for: " + ", ".join(missing),
            "missing_roles": missing,
            "metric": METRIC,
        }

    dates = pd.to_datetime(df[roles["date"]])
    first = pd.Timestamp(start)
    after_last = pd.Timestamp(end) + pd.Timedelta(days=1)  # a time on the last day still counts
    rows = df[(dates >= first) & (dates < after_last)]
    amount = roles["amount"]

    return {
        "status": "ok",
        "value": round(float(rows[amount].sum()), 2),
        "value_without_duplicates": round(float(rows.drop_duplicates()[amount].sum()), 2),
        "rows": int(len(rows)),
        "period": {"start": start, "end": end},
        "unit": "CAD",
        "metric": METRIC,
    }
