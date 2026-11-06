"""Find the role of each column (date, amount, customer...) from its name and its type."""

import pandas as pd

# Column names that mean each role, compared on letters and digits only, in order of preference.
# English and French: the user's file will not use our column names.
SYNONYMS = {
    "date": ["orderdate", "date", "invoicedate", "saledate", "salesdate", "transactiondate",
             "datedevente", "datevente", "datecommande", "datefacture"],
    "amount": ["amount", "salesamount", "linetotal", "netsales", "sales", "revenue", "total",
               "montant", "ventes", "totalligne"],
    "unit_price": ["unitprice", "price", "prixunitaire", "prix"],
    "quantity": ["quantity", "qty", "units", "quantite", "qte"],
    "order_id": ["orderid", "ordernumber", "orderno", "order", "invoiceid", "invoicenumber",
                 "invoice", "transactionid", "receipt", "nocommande", "numerocommande",
                 "commande", "facture"],
    "customer": ["customer", "customername", "client", "nomclient", "account", "buyer"],
    "product": ["product", "productname", "item", "itemname", "sku", "produit", "article",
                "description", "itemdescription", "productdescription", "designation"],
    "region": ["store", "storename", "region", "branch", "location", "shop", "outlet",
               "magasin", "succursale", "boutique", "territory", "territoire", "district",
               "zone", "country", "pays"],
}  # fmt: skip
# Words that rule a column out of a role whatever its name: a product line or category groups
# products, it is not a product (PRODUCTLINE next to PRODUCTCODE).
NOT_FOR = {"product": ["line", "categ", "type", "group", "family", "class", "famille", "gamme"]}
NUMERIC_ROLES = {"amount", "unit_price", "quantity"}
# Roles that name something. Real exports often write them as numbers (customer 13085, store 4).
IDENTIFIER_ROLES = {"order_id", "customer", "product", "region"}
TARGET_NAMES = ["target", "goal", "budget", "objective", "objectif", "cible"]
MONTH_NAMES = ["month", "mois", "period", "periode", "date"]


def key(name) -> str:
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def is_date(column: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(column):
        return True
    if pd.api.types.is_numeric_dtype(column):
        return False
    parsed = pd.to_datetime(column.dropna().head(200), errors="coerce", format="mixed")
    return len(parsed) > 0 and parsed.notna().mean() >= 0.9


def whole_numbers(column: pd.Series) -> bool:
    if pd.api.types.is_bool_dtype(column):
        return False
    values = column.dropna()
    return len(values) > 0 and bool((values == values.round()).all())


def fits(role: str, column: pd.Series) -> bool:
    if role == "date":
        return is_date(column)
    if role in NUMERIC_ROLES:
        return pd.api.types.is_numeric_dtype(column)
    if pd.api.types.is_numeric_dtype(column):
        # A number names something only if it is whole: 13085 can be a customer, 12.5 cannot.
        return role in IDENTIFIER_ROLES and whole_numbers(column)
    return True


def find(df: pd.DataFrame, names: list[str], taken: set, test) -> str | None:
    """The first column whose name matches, exactly first, then by containing a synonym."""
    keys = {column: key(column) for column in df.columns if column not in taken}
    for exact in (True, False):
        for name in names:
            for column, k in keys.items():
                match = k == name if exact else name in k
                if match and test(df[column]):
                    return column
    return None


def recognize_roles(orders: pd.DataFrame, other_sheets: dict | None = None) -> dict:
    """The column found for each role, or None. The target is "Sheet.column" in another sheet."""
    roles, taken = {}, set()
    for role, names in SYNONYMS.items():
        ruled_out = {c for c in orders.columns if any(w in key(c) for w in NOT_FOR.get(role, []))}
        column = find(orders, names, taken | ruled_out, lambda c, r=role: fits(r, c))
        roles[role] = column
        if column:
            taken.add(column)
    roles["target"] = None
    for sheet, df in (other_sheets or {}).items():
        column = find(df, TARGET_NAMES, set(), pd.api.types.is_numeric_dtype)
        if column:
            roles["target"] = f"{sheet}.{column}"
            break
    order = ["date", "amount", "customer", "product", "quantity", "unit_price", "region"]
    return {role: roles[role] for role in [*order, "order_id", "target"]}


def read_targets(other_sheets: dict, roles: dict) -> pd.DataFrame | None:
    """The target sheet as one row per month and store: columns month ("2025-03"), store, target."""
    if not roles.get("target"):
        return None
    sheet, column = roles["target"].split(".", 1)
    df = other_sheets[sheet]
    month = find(df, MONTH_NAMES, {column}, lambda c: True)
    store = find(df, SYNONYMS["region"], {column, month}, lambda c: True)
    if not month or not store:
        return None
    return pd.DataFrame(
        {
            "month": pd.to_datetime(df[month].astype(str), format="mixed").dt.strftime("%Y-%m"),
            "store": df[store],
            "target": df[column],
        }
    )
