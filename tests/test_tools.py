import json
from pathlib import Path

import pandas as pd

from api.tools import RUNNERS, TOOLS, Dataset, run_tool

ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
ROLES = {
    "date": "order_date",
    "amount": "amount",
    "customer": "customer",
    "order_id": "order_id",
    "region": "store",
}
STATCAN_ON = json.loads((DATA / "statcan_on_2026-10-23.json").read_text())


def session(file: str = "small_sales.csv", **extra) -> Dataset:
    df = pd.read_csv(DATA / file, parse_dates=["order_date"])
    return Dataset(df, ROLES, **extra)


def call(name: str, data: Dataset, **arguments) -> dict:
    return run_tool(name, json.dumps(arguments), data)


def test_there_is_one_tool_per_certified_metric():
    cards = {path.stem for path in (ROOT / "api" / "metrics").glob("*.yaml")}
    assert {tool["name"] for tool in TOOLS} == cards == set(RUNNERS)


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
    result = call("sales_total", session(), start="2025-01-01", end="2025-12-31")
    assert result["value"] == 480.75
    assert result["metric"]["name"] == "sales_total"


def test_store_null_means_the_whole_business():
    data = session("small_growth.csv")
    whole = call("sales_growth", data, start="2026-01-01", end="2026-03-31", store=None)
    online = call("sales_growth", data, start="2026-01-01", end="2026-03-31", store="Online")
    assert whole["value"] == 0.525
    assert online["value"] == -0.2


def test_ranking_arguments_reach_the_metric():
    result = call(
        "sales_ranking",
        session(),
        start="2025-01-01",
        end="2025-12-31",
        by="customer",
        n=2,
        store=None,
    )
    assert len(result["table"]["rows"]) == 2


def test_market_comparison_uses_the_province_of_the_session():
    data = session("small_growth.csv", province="ON", reference=STATCAN_ON)
    result = call("market_comparison", data, start="2026-01-01", end="2026-03-31", store=None)
    assert result["benchmark"].startswith("Ontario retail trade")
    assert result["published"] == "2026-08"


def test_market_comparison_without_a_benchmark_is_an_error():
    result = call("market_comparison", session(), start="2025-01-01", end="2025-12-31", store=None)
    assert result == {"status": "error", "reason": "No market benchmark for this session"}


def test_the_model_cannot_add_an_argument():
    result = call("sales_total", session(), start="2025-01-01", end="2025-12-31", path="/tmp/x")
    assert result["status"] == "error"


def test_an_unknown_tool_is_an_error():
    result = run_tool("profit_margin", "{}", session())
    assert result == {"status": "error", "reason": "Unknown tool: profit_margin"}


def test_a_bad_date_goes_back_to_the_model_as_an_error():
    result = call("sales_total", session(), start="2025-02-30", end="2025-12-31")
    assert result["status"] == "error"
