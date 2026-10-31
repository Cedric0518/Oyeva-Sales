"""Compute the reference answers (pandas oracle) for the Atlas sample.

Certified definitions used here (v1):
- sales = sum of amount, returns (negative lines) included, file taken as-is
  (duplicates are NOT silently removed; the value without them is also given);
- rows whose date is outside the file's expected period (after 2026-08-31) are ignored;
- customer metrics ignore the placeholder customer "Walk-in";
- a customer is "lost" if it bought in the reference period and not in the
  comparison period; "new" if the reverse; "retained" if both;
- average basket = sales / number of distinct order_id with a positive amount.
"""

import json
import sys
from pathlib import Path

import pandas as pd

DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "out/atlas")
orders = pd.read_excel(DIR / "atlas_sales.xlsx", sheet_name="Orders")
targets = pd.read_excel(DIR / "atlas_sales.xlsx", sheet_name="Targets")
orders["order_date"] = pd.to_datetime(orders.order_date)
valid = orders[orders.order_date <= "2026-08-31"].copy()
valid["month"] = valid.order_date.dt.strftime("%Y-%m")
valid["year"] = valid.order_date.dt.year
dedup = valid.drop_duplicates()


def r2(x):
    return round(float(x), 2)


ans = {}
ans["rows_in_file"] = int(len(orders))
ans["rows_out_of_range"] = int(len(orders) - len(valid))
ans["sales_by_year"] = {str(k): r2(v) for k, v in valid.groupby("year").amount.sum().items()}
ans["sales_by_year_without_duplicates"] = {
    str(k): r2(v) for k, v in dedup.groupby("year").amount.sum().items()
}
ans["sales_by_month"] = {k: r2(v) for k, v in valid.groupby("month").amount.sum().items()}
ans["sales_by_store_2025"] = {
    k: r2(v) for k, v in valid[valid.year == 2025].groupby("store").amount.sum().items()
}

ytd25 = valid[(valid.order_date >= "2025-01-01") & (valid.order_date <= "2025-08-31")]
ytd26 = valid[(valid.order_date >= "2026-01-01") & (valid.order_date <= "2026-08-31")]
ans["growth_jan_aug_2026_vs_2025"] = round(float(ytd26.amount.sum() / ytd25.amount.sum() - 1), 4)
ans["growth_jan_aug_2026_vs_2025_by_store"] = {
    s: round(
        float(ytd26[ytd26.store == s].amount.sum() / ytd25[ytd25.store == s].amount.sum() - 1), 4
    )
    for s in sorted(valid.store.unique())
}

y25 = valid[valid.year == 2025]
cust25 = (
    y25[y25.customer != "Walk-in"].groupby("customer").amount.sum().sort_values(ascending=False)
)
ans["top10_customers_2025"] = [[k, r2(v)] for k, v in cust25.head(10).items()]
ans["top10_share_2025"] = round(float(cust25.head(10).sum() / y25.amount.sum()), 4)
ans["walk_in_share_2025"] = round(
    float(y25[y25.customer == "Walk-in"].amount.sum() / y25.amount.sum()), 4
)
prod25 = y25.groupby("product").amount.sum().sort_values(ascending=False)
ans["top10_products_2025"] = [[k, r2(v)] for k, v in prod25.head(10).items()]


def customers(df):
    return set(df[(df.customer != "Walk-in") & (df.amount > 0)].customer)


c25, c26 = customers(ytd25), customers(ytd26)
ans["customers_jan_aug_2025_vs_2026"] = {
    "lost": len(c25 - c26),
    "new": len(c26 - c25),
    "retained": len(c25 & c26),
}
biz25 = {c for c in c25 if c in set(valid[valid.customer_type == "Business"].customer)}
biz26 = {c for c in c26 if c in set(valid[valid.customer_type == "Business"].customer)}
ans["business_accounts_lost_jan_aug_2026"] = sorted(biz25 - biz26)
ans["business_accounts_new_jan_aug_2026"] = sorted(biz26 - biz25)


def basket(df):
    pos = df[df.amount > 0]
    return r2(df.amount.sum() / pos.order_id.nunique())


ans["average_basket_by_year"] = {
    str(y): basket(valid[valid.year == y]) for y in sorted(valid.year.unique())
}

t = targets.copy()
act = valid.groupby(["month", "store"]).amount.sum().rename("actual").reset_index()
t = t.merge(act, on=["month", "store"], how="left")
tot = t.groupby("month")[["target", "actual"]].sum()
ans["target_attainment_by_month_total"] = {
    k: round(float(v.actual / v.target), 4) for k, v in tot.iterrows()
}
t25 = t[t.month.str.startswith("2025")].groupby("store")[["target", "actual"]].sum()
ans["target_attainment_2025_by_store"] = {
    k: round(float(v.actual / v.target), 4) for k, v in t25.iterrows()
}

# Checks oracle
ans["checks"] = {
    "duplicate_rows": int(orders.duplicated().sum()),
    "duplicate_amount": r2(orders[orders.duplicated()].amount.sum()),
    "amount_mismatch_rows": int(
        ((orders.quantity * orders.unit_price).round(2) - orders.amount).abs().gt(0.01).sum()
    ),
    "return_lines": int((orders.amount < 0).sum()),
    "return_amount": r2(orders[orders.amount < 0].amount.sum()),
    "dates_out_of_range": orders[orders.order_date > "2026-08-31"].order_id.tolist(),
    "months_without_sales": sorted(
        f"{s} {m}"
        for s in orders.store.unique()
        for m in sorted(valid.month.unique())
        if valid[(valid.store == s) & (valid.month == m)].empty
    ),
    "name_variant_groups": [
        ["Lakeshore Dental Clinic", "LAKESHORE DENTAL CLINIC INC.", "Lakeshore Dental Clinic Inc"]
    ],
    "placeholder_customer": "Walk-in",
}

# Story checks
ans["story"] = {
    "queen_street_feb_2025": r2(
        valid[(valid.store == "Toronto - Queen Street") & (valid.month == "2025-02")].amount.sum()
    ),
    "queen_street_mar_2025": r2(
        valid[(valid.store == "Toronto - Queen Street") & (valid.month == "2025-03")].amount.sum()
    ),
    "total_feb_2025": ans["sales_by_month"]["2025-02"],
    "total_mar_2025": ans["sales_by_month"]["2025-03"],
    "hamilton_jan_aug_2025": r2(ytd25[ytd25.store == "Hamilton"].amount.sum()),
    "hamilton_jan_aug_2026": r2(ytd26[ytd26.store == "Hamilton"].amount.sum()),
    "bayfront_2025": r2(y25[y25.customer == "Bayfront Elementary School"].amount.sum()),
}

(DIR / "answers.json").write_text(json.dumps(ans, indent=2))
print(
    json.dumps(
        {
            k: ans[k]
            for k in [
                "rows_in_file",
                "sales_by_year",
                "growth_jan_aug_2026_vs_2025",
                "growth_jan_aug_2026_vs_2025_by_store",
                "top10_share_2025",
                "walk_in_share_2025",
                "customers_jan_aug_2025_vs_2026",
                "business_accounts_lost_jan_aug_2026",
                "business_accounts_new_jan_aug_2026",
                "average_basket_by_year",
                "target_attainment_2025_by_store",
                "checks",
                "story",
            ]
        },
        indent=1,
    )
)
print("months:", {k: v for k, v in ans["sales_by_month"].items()})
