"""Reading uploaded sales files: Atlas against the contract, and the shapes of real exports."""

import io
import json
import re
from pathlib import Path

import pandas as pd
import pytest

from api.metrics.sales_ranking import sales_ranking
from api.metrics.sales_total import sales_total
from api.reading import DERIVED_AMOUNT, ReadError, read_sales_file

ROOT = Path(__file__).parent.parent
ATLAS = ROOT / "evals/data/atlas/atlas_sales.xlsx"
TODAY = "2026-11-05"


def read(text: str, name: str = "sales.csv", encoding: str = "utf-8", region: str = "ON"):
    return read_sales_file(text.encode(encoding), name, region, today=TODAY)


def warnings(read_file) -> dict:
    return {c["id"]: c["detail"] for c in read_file.response["checks"] if c["status"] != "ok"}


@pytest.fixture(scope="module")
def atlas():
    return read_sales_file(ATLAS.read_bytes(), ATLAS.name, "ON", today=TODAY)


def contract_example() -> dict:
    text = (ROOT / "docs/contract.md").read_text(encoding="utf-8")
    block = re.search(r"Response `200`:\n\n```json\n(.*?)\n```", text, re.S).group(1)
    return json.loads(block)


def test_atlas_gives_the_upload_response_of_the_contract(atlas):
    example = contract_example()
    for key in ("file_name", "sheets", "rows", "columns", "roles", "checks", "region"):
        assert atlas.response[key] == example[key], key
    assert re.fullmatch(r"ds_[0-9a-f]{16}", atlas.response["dataset_id"])
    preview = atlas.response["preview"]
    assert preview["columns"] == [c["name"] for c in example["columns"]]
    assert len(preview["rows"]) == 5


def test_the_contract_preview_row_is_a_row_of_atlas(atlas):
    example = contract_example()["preview"]
    df = atlas.data.df
    row = df[df["order_id"] == example["rows"][0][0]].iloc[0]
    values = [row[c] for c in example["columns"]]
    values[1] = values[1].date().isoformat()
    assert values == example["rows"][0]


def test_atlas_targets_and_description(atlas):
    assert atlas.data.targets.columns.tolist() == ["month", "store", "target"]
    assert atlas.data.province == "ON"
    assert "- Dates from 2024-09-01 to 2026-08-31." in atlas.description
    assert "Toronto - Queen Street" in atlas.description
    assert "sales_data.csv" in atlas.description


def test_the_session_csv_has_the_rows_as_read(atlas):
    df = pd.read_csv(io.BytesIO(atlas.csv))
    assert len(df) == 59764
    assert df["order_date"].iloc[0] == "2024-09-01"


def test_a_quebec_export_semicolons_decimal_comma_dollar_after_cp1252():
    text = (
        "Date de vente;Montant;Client;Magasin;No facture\n"
        "05/03/2025;1 234,50 $;Café Léa;Laval;F001\n"
        "13/03/2025;(12,00) $;Café Léa;Laval;F002\n"
        "02/04/2025;99,95 $;Épicerie Roy;Québec;F003\n"
    )
    result = read(text, "ventes.csv", "cp1252", "QC")
    df = result.data.df
    assert result.response["roles"]["amount"] == "Montant"
    assert df["Montant"].tolist() == [1234.5, -12.0, 99.95]
    assert df["Client"].tolist() == ["Café Léa", "Café Léa", "Épicerie Roy"]
    assert [d.isoformat() for d in df["Date de vente"].dt.date] == [
        "2025-03-05",
        "2025-03-13",
        "2025-04-02",
    ]
    assert sales_total(df, result.data.roles, "2025-01-01", "2025-12-31")["value"] == 1322.45


def test_quantity_and_unit_price_without_amount_give_a_computed_amount():
    text = (
        "Invoice,StockCode,Description,Quantity,InvoiceDate,Price,Customer ID,Country\n"
        "489434,85048,LED LIGHT,12,12/01/2009 07:45,6.95,13085,United Kingdom\n"
        "C489449,22087,PAPER BUNTING,-12,12/01/2009 10:33,2.95,16321,Australia\n"
        "489435,22350,CAT BOWL,12,12/13/2009 07:46,2.55,,United Kingdom\n"
    )
    result = read(text, "online_retail.csv")
    roles = result.response["roles"]
    assert roles["amount"] == DERIVED_AMOUNT
    assert roles["product"] == "Description"
    assert roles["customer"] == "Customer ID"
    assert roles["order_id"] == "Invoice"
    assert warnings(result)["derived_amount"] == (
        "No amount column: amount computed as Quantity x Price"
    )
    df = result.data.df
    assert df["Invoice"].tolist() == ["489434", "C489449", "489435"]  # stays text
    assert sales_total(df, result.data.roles, "2009-12-01", "2009-12-31")["value"] == 78.6
    ranking = sales_ranking(df, result.data.roles, "2009-12-01", "2009-12-31", by="customer", n=5)
    assert [row[0] for row in ranking["table"]["rows"]] == ["13085", "16321"]
    assert df["InvoiceDate"].iloc[1] == pd.Timestamp("2009-12-01 10:33")


def test_an_excel_report_with_a_title_above_the_header_and_a_total_row():
    rows = [["Sales report 2025", None, None], [None, None, None], ["Date", "Store", "Sales"]]
    rows += [
        [f"2025-01-{d:02d}", "North" if d % 2 else "South", f"{d * 100:,.2f}"] for d in range(1, 29)
    ]
    rows += [["Total", None, "40,600.00"]]
    content = io.BytesIO()
    pd.DataFrame(rows).to_excel(content, header=False, index=False)
    result = read_sales_file(content.getvalue(), "report.xlsx", "ON", today=TODAY)
    assert result.response["roles"]["date"] == "Date"
    assert result.response["roles"]["region"] == "Store"
    assert warnings(result) == {"unreadable_dates": "1 row with a Date that is not a date"}
    total = sales_total(result.data.df, result.data.roles, "2025-01-01", "2025-12-31")
    assert total["value"] == 40600.0  # the total row has no date: never counted


def test_dates_that_read_both_ways_are_reported():
    result = read("date,amount\n03/04/2025,10\n05/06/2025,20\n")
    assert warnings(result)["ambiguous_dates"] == (
        "Dates such as 03/04 in date were read as month/day"
    )


def test_month_names_and_codes_with_leading_zeros_stay_text():
    result = read("date,month,code,amount\n2025-03-04,March,00123,10\n2025-06-05,June,00456,20\n")
    types = {c["name"]: c["type"] for c in result.response["columns"]}
    assert types == {"date": "date", "month": "text", "code": "text", "amount": "number"}


def test_a_column_with_one_word_among_numbers_stays_text():
    result = read("date,amount\n2025-01-02,10\n2025-01-03,ten\n")
    assert result.response["roles"]["amount"] is None
    assert result.response["checks"][0]["status"] == "error"


@pytest.mark.parametrize(
    ("content", "name", "code"),
    [
        (b"%PDF-1.4", "notes.pdf", "unsupported_format"),
        (b"not an excel file", "sales.xlsx", "unreadable_file"),
        (b"", "empty.csv", "unreadable_file"),
        (b"one column\n1\n2\n", "one.csv", "unreadable_file"),
    ],
)
def test_files_the_api_cannot_read(content, name, code):
    with pytest.raises(ReadError) as error:
        read_sales_file(content, name, "ON")
    assert error.value.code == code


def test_a_kaggle_style_export_capitals_windows_encoding_product_line_and_territory():
    text = (
        "ORDERNUMBER,QUANTITYORDERED,PRICEEACH,SALES,ORDERDATE,PRODUCTLINE,PRODUCTCODE,"
        "CUSTOMERNAME,COUNTRY,TERRITORY\n"
        "10107,30,95.7,2871,2/24/2003 0:00,Motorcycles,S10_1678,Land of Toys Inc.,USA,NA\n"
        "10121,34,81.35,2765.9,5/7/2003 0:00,Motorcycles,S10_1678,Reims Collectables,France,EMEA\n"
        "10134,41,94.74,3884.34,7/1/2003 0:00,Classic Cars,S10_1949,Lyon Souveniers,France,EMEA\n"
        "10145,45,100,5205.27,8/25/2003 0:00,Classic Cars,S10_1949,Société Générale,France,EMEA\n"
    )
    result = read(text, "sales_data_sample.csv", "cp1252")
    roles = result.response["roles"]
    assert roles["product"] == "PRODUCTCODE"  # PRODUCTLINE groups products
    assert roles["region"] == "TERRITORY"
    assert roles["order_id"] == "ORDERNUMBER"
    assert result.data.df["ORDERDATE"].iloc[0] == pd.Timestamp("2003-02-24")
    assert "ambiguous_dates" not in warnings(result)  # 2/24 tells month from day
    assert warnings(result)["amount_mismatch"] == "1 row"  # 45 x 100 is not 5205.27
    assert result.data.df["CUSTOMERNAME"].iloc[3] == "Société Générale"


def test_the_description_tells_the_agent_the_checks_with_a_warning(atlas):
    assert "- Checks with a warning:" in atlas.description
    assert "  - Months without sales: Online: 2025-07." in atlas.description
    assert "  - Duplicate rows: 12 duplicate rows." in atlas.description
    assert "Returns" not in atlas.description  # an ok check is not listed
