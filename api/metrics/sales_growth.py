"""Certified metric: year-over-year growth. The definition lives in the .yaml card."""

import pandas as pd

from api.metrics.common import check_inputs, in_period, load_card, refusal

CARD = load_card(__file__)
ONE_YEAR = pd.DateOffset(years=1)


def growth(current: float, previous: float) -> float | None:
    return round(current / previous - 1, 4) if previous else None


def sales_growth(
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

    date, amount = roles["date"], roles["amount"]
    current = in_period(df, date, start, end)
    previous = in_period(df, date, previous_period["start"], previous_period["end"])

    # The month of each row; the previous year moved forward by 12 months to line up.
    current_months = pd.to_datetime(current[date]).dt.to_period("M")
    previous_months = pd.to_datetime(previous[date]).dt.to_period("M") + 12
    in_current, in_previous = set(current_months), set(previous_months)
    comparable, left_out = [], []
    for month in pd.period_range(first, last, freq="M"):
        if month in in_current and month in in_previous:
            comparable.append(month)
        elif month in in_current:
            left_out.append(str(month - 12))
        elif month in in_previous:
            left_out.append(str(month))
    if not comparable:
        return refusal(CARD, "No month has sales in both years", previous=previous_period)

    now = current[current_months.isin(comparable)]
    before = previous[previous_months.isin(comparable)]
    return {
        "status": "ok",
        "value": growth(now[amount].sum(), before[amount].sum()),
        "value_without_duplicates": growth(
            now.drop_duplicates()[amount].sum(), before.drop_duplicates()[amount].sum()
        ),
        "value_all_months": growth(current[amount].sum(), previous[amount].sum()),
        "months_left_out": left_out,
        "current": {
            "start": start,
            "end": end,
            "comparable_sales": round(float(now[amount].sum()), 2),
        },
        "previous": {**previous_period, "comparable_sales": round(float(before[amount].sum()), 2)},
        "metric": CARD["metric"],
    }
