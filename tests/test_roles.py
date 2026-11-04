import pandas as pd

from api.checks.roles import read_targets, recognize_roles


def test_english_column_names():
    df = pd.DataFrame(
        {
            "order_id": ["A1"],
            "order_date": ["2025-01-02"],
            "store": ["Main"],
            "customer": ["Alpha Co"],
            "customer_type": ["Business"],
            "product": ["Pen"],
            "quantity": [2],
            "unit_price": [3.5],
            "amount": [7.0],
        }
    )
    assert recognize_roles(df) == {
        "date": "order_date",
        "amount": "amount",
        "customer": "customer",
        "product": "product",
        "quantity": "quantity",
        "unit_price": "unit_price",
        "region": "store",
        "order_id": "order_id",
        "target": None,
    }


def test_french_column_names():
    df = pd.DataFrame(
        {
            "Date de vente": ["2025-01-02"],
            "Montant": [10.0],
            "Client": ["Alpha"],
            "Magasin": ["Laval"],
            "No commande": ["1"],
        }
    )
    roles = recognize_roles(df)
    assert roles["date"] == "Date de vente"
    assert roles["amount"] == "Montant"
    assert roles["customer"] == "Client"
    assert roles["region"] == "Magasin"
    assert roles["order_id"] == "No commande"


def test_a_text_column_is_never_the_amount():
    df = pd.DataFrame({"date": ["2025-01-02"], "total": ["ten dollars"]})
    assert recognize_roles(df)["amount"] is None


def test_target_in_another_sheet():
    orders = pd.DataFrame({"date": ["2025-01-02"], "amount": [10.0], "store": ["Main"]})
    sheets = {"Goals": pd.DataFrame({"month": ["2025-01"], "store": ["Main"], "goal": [100]})}
    roles = recognize_roles(orders, sheets)
    assert roles["target"] == "Goals.goal"
    targets = read_targets(sheets, roles)
    assert targets.to_dict("records") == [{"month": "2025-01", "store": "Main", "target": 100}]
