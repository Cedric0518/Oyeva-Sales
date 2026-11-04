"""Certified metric: sales against target. The definition lives in the .yaml card."""

import pandas as pd

from api.metrics.common import check_inputs, in_period, load_card, refusal

CARD = load_card(__file__)


def ratio(actual: float, target: float) -> float | None:
    return round(float(actual / target), 4) if target else None


def target_attainment(
    df: pd.DataFrame,
    roles: dict,
    start: str,
    end: str,
    targets: pd.DataFrame | None,
    store: str | None = None,
) -> dict:
    """`targets`: one row per month and store, columns month ("2025-03"), store and target."""
    refused = check_inputs(CARD, df, roles, store)
    if refused:
        return refused
    if targets is None or targets.empty:
        return refusal(CARD, "The file has no targets")
    if store:
        df = df[df[roles["region"]] == store]
        targets = targets[targets["store"] == store]

    months = [str(p) for p in pd.period_range(start, end, freq="M")]
    goals = targets[targets["month"].isin(months)]
    if goals.empty:
        return refusal(CARD, "The file has no target in this period")

    date, amount, region = roles["date"], roles["amount"], roles["region"]
    rows = in_period(df, date, start, end)
    month = pd.to_datetime(rows[date]).dt.strftime("%Y-%m").rename("month")
    actual = rows.groupby([month, rows[region].rename("store")])[amount].sum().rename("actual")
    merged = goals.merge(actual.reset_index(), on=["month", "store"], how="left")

    no_rows = merged["actual"].isna()
    left_out = (merged["store"][no_rows] + " " + merged["month"][no_rows]).tolist()
    kept = merged[~no_rows]
    by_month = kept.groupby("month")[["actual", "target"]].sum()

    def row(m: str) -> list:
        if m not in by_month.index:
            return [m, None, None, None]
        sold, goal = by_month.at[m, "actual"], by_month.at[m, "target"]
        return [m, round(float(sold), 2), float(goal), ratio(sold, goal)]

    table_rows = [row(m) for m in sorted(goals["month"].unique())]
    title = "Sales against target" + (f", {store}" if store else "")
    return {
        "status": "ok",
        "value": ratio(kept["actual"].sum(), kept["target"].sum()),
        "value_all_months": ratio(merged["actual"].fillna(0).sum(), merged["target"].sum()),
        "left_out": sorted(left_out),
        "chart": {
            "type": "line",
            "title": title,
            "x": {"label": "Month", "values": [r[0] for r in table_rows]},
            "series": [
                {"name": "Sales", "values": [r[1] for r in table_rows]},
                {"name": "Target", "values": [r[2] for r in table_rows], "style": "dashed"},
            ],
            "unit": "CAD",
        },
        "table": {
            "title": title,
            "columns": ["Month", "Sales", "Target", "Attainment"],
            "rows": table_rows,
        },
        "period": {"start": start, "end": end},
        "unit": "CAD",
        "metric": CARD["metric"],
    }
