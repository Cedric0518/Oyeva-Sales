"""Certified metric: top customers or products. The definition lives in the .yaml card."""

import pandas as pd

from api.metrics.common import check_inputs, in_period, is_placeholder, load_card, refusal

CARD = load_card(__file__)
LABELS = {"customer": "Customer", "product": "Product"}


def money(amount) -> float:
    return round(float(amount), 2)


def share(part, total) -> float | None:
    return round(float(part / total), 4) if total else None


def sales_ranking(
    df: pd.DataFrame,
    roles: dict,
    start: str,
    end: str,
    by: str = "customer",
    n: int = 10,
    store: str | None = None,
) -> dict:
    if by not in LABELS:
        return refusal(CARD, f"Unknown ranking: {by}", rankings=list(LABELS))
    refused = check_inputs(CARD, df, roles, store, extra=(by,))
    if refused:
        return refused
    if not 1 <= n <= 50:
        return refusal(CARD, "The number of items must be between 1 and 50")
    if store:
        df = df[df[roles["region"]] == store]

    rows = in_period(df, roles["date"], start, end)
    if rows.empty:
        return refusal(CARD, "The file has no rows in this period")

    amount, column = roles["amount"], roles[by]
    total = rows[amount].sum()
    if by == "customer":
        left_out = rows[column].map(is_placeholder)
    else:
        left_out = rows[column].isna()
    ranked = rows[~left_out]

    sales = ranked.groupby(column)[amount].sum()
    unique = ranked.drop_duplicates().groupby(column)[amount].sum()
    # Sorted by name first, then a stable sort by sales: equal sales stay in name order.
    top = sales.sort_index().sort_values(ascending=False, kind="stable").head(n)

    label = LABELS[by]
    names = [str(name) for name in top.index]
    title = f"Top {len(names)} {label.lower()}s" + (f", {store}" if store else "")
    left_out_names = {"(no name)" if pd.isna(x) else str(x) for x in rows.loc[left_out, column]}
    left_out_sales = rows.loc[left_out, amount].sum()
    return {
        "status": "ok",
        "chart": {
            "type": "bar_horizontal",
            "title": title,
            "x": {"label": label, "values": names},
            "series": [{"name": "Sales", "values": [money(value) for value in top]}],
            "unit": "CAD",
        },
        "table": {
            "title": title,
            "columns": [label, "Sales", "Share of sales", "Sales without duplicates"],
            "rows": [
                [str(name), money(value), share(value, total), money(unique[name])]
                for name, value in top.items()
            ],
        },
        "top_share": share(top.sum(), total),
        "left_out": {
            "names": sorted(left_out_names),
            "sales": money(left_out_sales),
            "share": share(left_out_sales, total),
        },
        "total_sales": money(total),
        "period": {"start": start, "end": end},
        "unit": "CAD",
        "metric": CARD["metric"],
    }
