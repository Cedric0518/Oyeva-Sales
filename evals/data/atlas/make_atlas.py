"""Generate the Atlas General Store sample data for Oyeva Sales.

Fictional Ontario general retailer: 4 stores + online, Sep 2024 to Aug 2026.
Outputs (in OUT_DIR): atlas_sales.xlsx (Orders, Targets), atlas_orders.csv,
defects.json (the defects planted on purpose, for the checks oracle).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "out/atlas")
OUT_DIR.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2024-09-01")
END = pd.Timestamp("2026-08-31")
DAYS = pd.date_range(START, END, freq="D")

STORES = {
    "Toronto - Queen Street": {"base": 9.0, "growth": 0.03},
    "Mississauga": {"base": 7.0, "growth": 0.03},
    "Hamilton": {"base": 5.5, "growth": 0.03},
    "Ottawa": {"base": 5.5, "growth": 0.03},
    "Online": {"base": 3.0, "growth": 0.25},
}
MONTH_FACTOR = {
    1: 0.82,
    2: 0.85,
    3: 0.95,
    4: 0.98,
    5: 1.02,
    6: 1.03,
    7: 1.00,
    8: 1.08,
    9: 1.05,
    10: 1.00,
    11: 1.15,
    12: 1.38,
}
WEEKDAY_FACTOR = [0.85, 0.90, 0.95, 1.00, 1.10, 1.30, 0.90]  # Mon..Sun

QUEEN_CLOSED = (pd.Timestamp("2025-03-03"), pd.Timestamp("2025-03-28"))
HAMILTON_COMPETITOR = pd.Timestamp("2026-01-01")  # not documented on purpose
GROCERY_PRICE_CHANGE = pd.Timestamp("2025-06-01")
BLACK_FRIDAY = [
    (pd.Timestamp("2024-11-29"), pd.Timestamp("2024-12-02")),
    (pd.Timestamp("2025-11-28"), pd.Timestamp("2025-12-01")),
]

PRODUCTS = [
    # name, category, base price
    ("Whole wheat bread", "Grocery", 3.49),
    ("Organic eggs, dozen", "Grocery", 6.99),
    ("Coffee beans 1 kg", "Grocery", 18.99),
    ("Oat milk 1.89 L", "Grocery", 4.99),
    ("Pasta 900 g", "Grocery", 2.79),
    ("Olive oil 1 L", "Grocery", 12.99),
    ("Granola bars, box of 12", "Grocery", 6.49),
    ("Sparkling water, 12 pack", "Grocery", 7.99),
    ("Laundry detergent 4 L", "Household", 14.99),
    ("Paper towels, 6 rolls", "Household", 9.99),
    ("Dish soap 1 L", "Household", 4.49),
    ("Trash bags, 40 count", "Household", 11.99),
    ("LED bulbs, 4 pack", "Household", 12.99),
    ("Vitamin D, 120 tablets", "Health and beauty", 11.99),
    ("Sunscreen SPF 50", "Health and beauty", 13.99),
    ("Shampoo 750 ml", "Health and beauty", 8.99),
    ("Toothpaste, 2 pack", "Health and beauty", 6.99),
    ("Pain relief tablets, 100", "Health and beauty", 10.49),
    ("Hand sanitizer 1 L", "Health and beauty", 9.49),
    ("Printer paper, 5 reams", "Office and school", 42.00),
    ("Ballpoint pens, 24 pack", "Office and school", 8.99),
    ("Notebooks, 5 pack", "Office and school", 9.49),
    ("Ink cartridge, black", "Office and school", 34.99),
    ("Backpack", "Office and school", 39.99),
    ("Sticky notes, 12 pads", "Office and school", 11.99),
    ("Patio string lights", "Seasonal", 29.99),
    ("Snow shovel", "Seasonal", 34.99),
    ("Holiday gift wrap set", "Seasonal", 14.99),
    ("Beach towel", "Seasonal", 19.99),
    ("Ice melt 10 kg", "Seasonal", 16.99),
    ("Halloween candy, 100 pieces", "Seasonal", 19.99),
    ("Board game", "Toys and games", 34.99),
    ("Puzzle 1000 pieces", "Toys and games", 21.99),
    ("Building blocks set", "Toys and games", 49.99),
]
CAT_WEIGHT = {
    "Grocery": 0.38,
    "Household": 0.18,
    "Health and beauty": 0.18,
    "Office and school": 0.08,
    "Seasonal": 0.10,
    "Toys and games": 0.08,
}
SEASONAL_MONTHS = {
    "Snow shovel": {11, 12, 1, 2, 3},
    "Ice melt 10 kg": {11, 12, 1, 2, 3},
    "Patio string lights": {5, 6, 7, 8},
    "Beach towel": {5, 6, 7, 8},
    "Holiday gift wrap set": {11, 12},
    "Halloween candy, 100 pieces": {9, 10},
}

BUSINESSES = [
    # name, home store, orders per month, size factor, active from, active to
    ("Lakeshore Dental Clinic", "Toronto - Queen Street", 4, 1.4, None, None),
    ("Kingsway Law Office", "Toronto - Queen Street", 3, 1.2, None, None),
    ("Harbour Physio Centre", "Toronto - Queen Street", 2, 0.9, None, None),
    ("Riverside Community Centre", "Toronto - Queen Street", 2, 1.1, None, None),
    ("Spadina Print Studio", "Toronto - Queen Street", 3, 1.0, None, "2025-08-31"),
    ("Maple Ridge Daycare", "Mississauga", 4, 1.1, None, None),
    ("Cooksville Medical Group", "Mississauga", 3, 1.3, None, None),
    ("Port Credit Rowing Club", "Mississauga", 1, 0.8, None, None),
    ("Meadowvale Tutoring Centre", "Mississauga", 2, 0.9, "2025-04-01", None),
    ("Bayfront Elementary School", "Hamilton", 4, 1.3, None, "2025-12-31"),
    ("Westdale Veterinary Clinic", "Hamilton", 2, 1.0, None, None),
    ("Locke Street Cafe", "Hamilton", 4, 0.9, None, None),
    ("Dundurn Accounting", "Hamilton", 2, 0.8, None, None),
    ("Northgate Library Branch", "Ottawa", 3, 1.2, None, None),
    ("Pinecrest Seniors Residence", "Ottawa", 4, 1.5, None, None),
    ("Glebe Yoga Studio", "Ottawa", 2, 0.7, None, None),
    ("Rideau Engineering", "Ottawa", 2, 1.1, None, None),
    ("Greenline Architects", "Ottawa", 4, 1.6, "2026-03-01", None),
    ("Byward Market Bistro", "Ottawa", 3, 0.9, None, "2026-02-28"),
]

GROCERY_UP = 1.05


def unit_price(base, category, day):
    price = base * (GROCERY_UP if category == "Grocery" and day >= GROCERY_PRICE_CHANGE else 1.0)
    return round(price, 2)


def years_since_start(day):
    return (day - START).days / 365.25


def product_weights(month, b2b=False):
    w = []
    for name, cat, _ in PRODUCTS:
        if name in SEASONAL_MONTHS and month not in SEASONAL_MONTHS[name]:
            w.append(0.0)
            continue
        if b2b:
            base = {
                "Grocery": 0.25,
                "Household": 0.25,
                "Health and beauty": 0.10,
                "Office and school": 0.40,
                "Seasonal": 0.0,
                "Toys and games": 0.0,
            }[cat]
        else:
            base = CAT_WEIGHT[cat]
            if cat == "Office and school" and month in (8, 9):
                base *= 2.5
            if cat == "Toys and games" and month in (11, 12):
                base *= 2.5
            if name == "Sunscreen SPF 50" and month in (5, 6, 7, 8):
                base *= 3.0
            if name == "Halloween candy, 100 pieces" and month == 10:
                base *= 3.0
        w.append(base)
    w = np.array(w)
    return w / w.sum()


def is_black_friday(day):
    return any(a <= day <= b for a, b in BLACK_FRIDAY)


def simulate(rng, disruptions=True):
    """Return a list of order lines (dicts) before defects."""
    # Loyalty members: home store, start and end of activity, weight.
    members = []
    mid = 100000
    for store in STORES:
        n = {"Online": 500}.get(store, 600)
        for _ in range(n):
            mid += 1
            start = START + pd.Timedelta(days=int(rng.uniform(-730, 700)))
            end = start + pd.Timedelta(days=int(rng.exponential(720)))
            members.append((f"Loyalty L-{mid}", store, start, end, rng.gamma(0.8, 1.0)))
    members_by_store = {s: [m for m in members if m[1] == s] for s in STORES}

    lines = []
    order_seq = 1
    for day in DAYS:
        m = day.month
        pw_b2c = product_weights(m)
        for store, cfg in STORES.items():
            lam = cfg["base"] * MONTH_FACTOR[m] * (1 + cfg["growth"]) ** years_since_start(day)
            lam *= 1.0 if store == "Online" else WEEKDAY_FACTOR[day.weekday()]
            if is_black_friday(day):
                lam *= 3.0 if store == "Online" else 2.0
            if disruptions:
                if store == "Toronto - Queen Street" and QUEEN_CLOSED[0] <= day <= QUEEN_CLOSED[1]:
                    lam = 0.0
                if store == "Hamilton" and day >= HAMILTON_COMPETITOR:
                    lam *= 0.88
            n_orders = rng.poisson(lam)
            active = [x for x in members_by_store[store] if x[2] <= day <= x[3]]
            act_w = np.array([x[4] for x in active]) if active else None
            if act_w is not None:
                act_w = act_w / act_w.sum()
            for _ in range(n_orders):
                if store != "Online" and (not active or rng.random() < 0.55):
                    customer = "Walk-in"
                else:
                    customer = active[rng.choice(len(active), p=act_w)][0] if active else "Walk-in"
                oid = f"A{order_seq:07d}"
                order_seq += 1
                n_lines = rng.choice([1, 2, 3, 4, 5], p=[0.35, 0.28, 0.18, 0.12, 0.07])
                for idx in rng.choice(len(PRODUCTS), size=n_lines, replace=False, p=pw_b2c):
                    name, cat, base = PRODUCTS[idx]
                    q = int(rng.choice([1, 2, 3], p=[0.75, 0.18, 0.07]))
                    p = unit_price(base, cat, day)
                    lines.append(
                        dict(
                            order_id=oid,
                            order_date=day,
                            store=store,
                            channel="Online" if store == "Online" else "In-store",
                            customer=customer,
                            customer_type="Retail",
                            product=name,
                            category=cat,
                            quantity=q,
                            unit_price=p,
                            amount=round(q * p, 2),
                        )
                    )
        # Business accounts order on weekdays only.
        if day.weekday() < 5:
            pw_b2b = product_weights(m, b2b=True)
            for name_b, store, per_month, size, a_from, a_to in BUSINESSES:
                if disruptions:
                    if a_from and day < pd.Timestamp(a_from):
                        continue
                    if a_to and day > pd.Timestamp(a_to):
                        continue
                else:
                    if a_from:  # the plan does not know future new accounts
                        continue
                    if a_to and name_b != "Bayfront Elementary School" and day > pd.Timestamp(a_to):
                        continue
                if (
                    disruptions
                    and store == "Toronto - Queen Street"
                    and QUEEN_CLOSED[0] <= day <= QUEEN_CLOSED[1]
                ):
                    continue
                if rng.random() > per_month / 21.7:
                    continue
                oid = f"A{order_seq:07d}"
                order_seq += 1
                n_lines = int(rng.integers(3, 8))
                for idx in rng.choice(len(PRODUCTS), size=n_lines, replace=False, p=pw_b2b):
                    pname, cat, base = PRODUCTS[idx]
                    q = max(1, int(round(rng.gamma(2.0, 2.5) * size)))
                    p = unit_price(base, cat, day)
                    lines.append(
                        dict(
                            order_id=oid,
                            order_date=day,
                            store=store,
                            channel="In-store",
                            customer=name_b,
                            customer_type="Business",
                            product=pname,
                            category=cat,
                            quantity=q,
                            unit_price=p,
                            amount=round(q * p, 2),
                        )
                    )
    return lines, order_seq


def main():
    rng = np.random.default_rng(20261031)
    lines, order_seq = simulate(rng, disruptions=True)
    orders = pd.DataFrame(lines)

    # Returns: 1.5% of retail lines come back within 1 to 25 days.
    retail = orders[orders.customer_type == "Retail"]
    ret_idx = rng.choice(retail.index, size=int(len(retail) * 0.015), replace=False)
    returns = []
    for i in ret_idx:
        r = orders.loc[i]
        d = r.order_date + pd.Timedelta(days=int(rng.integers(1, 26)))
        if d > END:
            continue
        if r.store == "Toronto - Queen Street" and QUEEN_CLOSED[0] <= d <= QUEEN_CLOSED[1]:
            continue
        returns.append(
            dict(
                order_id=f"R{order_seq:07d}",
                order_date=d,
                store=r.store,
                channel=r.channel,
                customer=r.customer,
                customer_type=r.customer_type,
                product=r["product"],
                category=r.category,
                quantity=-int(r.quantity),
                unit_price=r.unit_price,
                amount=-round(r.quantity * r.unit_price, 2),
            )
        )
        order_seq += 1
    orders = pd.concat([orders, pd.DataFrame(returns)], ignore_index=True)

    # Defect: online export missing for July 2025 (sales happened, file lacks them).
    july = (orders.store == "Online") & (orders.order_date.dt.strftime("%Y-%m") == "2025-07")
    online_july_removed = float(orders.loc[july, "amount"].sum())
    orders = orders[~july].reset_index(drop=True)

    defects = {"online_july_2025_missing_amount": round(online_july_removed, 2)}

    # Defect: customer name written three ways.
    lake = orders.index[orders.customer == "Lakeshore Dental Clinic"]
    pick = rng.choice(lake, size=18, replace=False)
    orders.loc[pick[:9], "customer"] = "LAKESHORE DENTAL CLINIC INC."
    orders.loc[pick[9:], "customer"] = "Lakeshore Dental Clinic Inc"
    defects["name_variants"] = {
        "Lakeshore Dental Clinic": ["LAKESHORE DENTAL CLINIC INC.", "Lakeshore Dental Clinic Inc"],
        "rows_changed": 18,
    }

    # Defect: quantity x unit_price does not match amount on 40 lines.
    pos = orders.index[(orders.quantity > 0) & (orders.customer_type == "Retail")]
    bad = rng.choice(pos, size=40, replace=False)
    for k, i in enumerate(bad):
        if k < 8:
            orders.loc[i, "amount"] = round(orders.loc[i, "amount"] * 10, 2)
        else:
            orders.loc[i, "amount"] = round(
                orders.loc[i, "amount"] + float(rng.choice([-1, 1]) * rng.integers(1, 20)), 2
            )
    defects["amount_mismatch_rows"] = 40

    # Defect: two dates typed with the wrong year (2052 instead of 2025).
    in_2025 = orders.index[orders.order_date.dt.year == 2025]
    typo = rng.choice(in_2025, size=2, replace=False)
    for i in typo:
        d = orders.loc[i, "order_date"]
        orders.loc[i, "order_date"] = d.replace(year=2052)
    defects["out_of_range_dates"] = [str(orders.loc[i, "order_id"]) for i in typo]

    # Defect: 12 exact duplicate rows.
    dup = rng.choice(orders.index[orders.quantity > 0], size=12, replace=False)
    dup_rows = orders.loc[dup]
    defects["duplicate_rows"] = 12
    defects["duplicate_amount"] = round(float(dup_rows.amount.sum()), 2)
    orders = pd.concat([orders, dup_rows], ignore_index=True)

    orders = orders.sort_values(["order_date", "order_id"], kind="stable").reset_index(drop=True)
    orders["order_date"] = orders.order_date.dt.date

    # Targets: a "normal year" plan (no closure, no competitor, no new accounts) + 4%.
    plan_lines, _ = simulate(np.random.default_rng(7), disruptions=False)
    plan = pd.DataFrame(plan_lines)
    plan["month"] = plan.order_date.dt.strftime("%Y-%m")
    # Calibrate the plan on the two stores without incidents in 2025.
    calm = ["Mississauga", "Ottawa"]
    act = pd.DataFrame(lines)
    act_calm = act[(act.store.isin(calm)) & (act.order_date.dt.year == 2025)].amount.sum()
    plan_calm = plan[(plan.store.isin(calm)) & (plan.order_date.dt.year == 2025)].amount.sum()
    factor = act_calm / plan_calm
    targets = (plan.groupby(["month", "store"]).amount.sum() * factor * 1.04 / 500).round() * 500
    targets = targets.reset_index().rename(columns={"amount": "target"})
    targets = targets[targets.month >= "2025-01"].reset_index(drop=True)

    with pd.ExcelWriter(OUT_DIR / "atlas_sales.xlsx", engine="openpyxl") as xw:
        orders.to_excel(xw, sheet_name="Orders", index=False)
        targets.to_excel(xw, sheet_name="Targets", index=False)
    orders.to_csv(OUT_DIR / "atlas_orders.csv", index=False)
    (OUT_DIR / "defects.json").write_text(json.dumps(defects, indent=2))
    print("rows", len(orders), "orders", orders.order_id.nunique(), "targets", len(targets))
    print(json.dumps(defects, indent=2))


if __name__ == "__main__":
    main()
