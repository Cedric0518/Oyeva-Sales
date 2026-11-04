import json
from pathlib import Path

import pandas as pd

from api.tools import TOOLS, Dataset, run_tool

DATA = Path(__file__).parent / "data"
ROLES = {"date": "order_date", "amount": "amount"}


def small_sales() -> Dataset:
    return Dataset(pd.read_csv(DATA / "small_sales.csv", parse_dates=["order_date"]), ROLES)


def test_every_tool_follows_strict_mode():
    for tool in TOOLS:
        parameters = tool["parameters"]
        assert tool["strict"] is True
        assert parameters["additionalProperties"] is False
        assert parameters["required"] == list(parameters["properties"])


def test_no_tool_lets_the_model_choose_a_file():
    for tool in TOOLS:
        for name in tool["parameters"]["properties"]:
            assert "file" not in name and "path" not in name


def test_sales_total_runs_on_the_session_data():
    arguments = json.dumps({"start": "2025-01-01", "end": "2025-12-31"})
    result = run_tool("sales_total", arguments, small_sales())
    assert result["value"] == 480.75
    assert result["metric"]["name"] == "sales_total"


def test_an_unknown_tool_is_an_error():
    result = run_tool("profit_margin", "{}", small_sales())
    assert result == {"status": "error", "reason": "Unknown tool: profit_margin"}


def test_a_bad_date_goes_back_to_the_model_as_an_error():
    arguments = json.dumps({"start": "2025-02-30", "end": "2025-12-31"})
    result = run_tool("sales_total", arguments, small_sales())
    assert result["status"] == "error"
