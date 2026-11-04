"""The certified metrics as function tools: what the agent sees, and how the API runs them.

The model only chooses the arguments of a call (a period, a store, a ranking). The data, the
column roles, the targets, the province and the Statistics Canada copy belong to the session:
the API sets them, never the model.
"""

import json
from dataclasses import dataclass

import pandas as pd

from api.metrics import (
    average_basket,
    customer_retention,
    market_comparison,
    sales_by_period,
    sales_growth,
    sales_ranking,
    sales_total,
    target_attainment,
)


@dataclass
class Dataset:
    """What the API holds for the session. None of it is sent to the model."""

    df: pd.DataFrame
    roles: dict
    targets: pd.DataFrame | None = None
    province: str | None = None
    reference: dict | None = None


START = {"type": "string", "description": "First day of the period, YYYY-MM-DD."}
END = {"type": "string", "description": "Last day of the period, YYYY-MM-DD, included."}
STORE = {
    "type": ["string", "null"],
    "description": "A store exactly as named in the file, or null for the whole business. "
    "An unknown store is refused with the list of stores.",
}


def function_tool(card: dict, use_for: str, properties: dict) -> dict:
    """A function tool in strict mode: every parameter is required, no other one is accepted."""
    return {
        "type": "function",
        "name": card["name"],
        "description": f"{use_for} Certified definition: {card['definition']}",
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        },
        "strict": True,
    }


TOOLS = [
    function_tool(
        sales_total.CARD,
        "Total sales over a period. Use it for any question about how much was sold.",
        {"start": START, "end": END},
    ),
    function_tool(
        sales_by_period.CARD,
        "Sales for each month, quarter or year of a period, as a chart. Use it to show how "
        "sales moved over time.",
        {
            "start": START,
            "end": END,
            "granularity": {"type": "string", "enum": ["month", "quarter", "year"]},
            "store": STORE,
        },
    ),
    function_tool(
        sales_growth.CARD,
        "Growth against the same dates one year earlier, for a period of one year or less. "
        "Use it for questions such as: are we selling more than last year?",
        {"start": START, "end": END, "store": STORE},
    ),
    function_tool(
        sales_ranking.CARD,
        "Top customers or top products over a period, with the share of the top ones in sales. "
        "Use it for: biggest customers, best-selling products, do we depend on a few customers?",
        {
            "start": START,
            "end": END,
            "by": {"type": "string", "enum": ["customer", "product"]},
            "n": {"type": "integer", "description": "How many to list, usually 10."},
            "store": STORE,
        },
    ),
    function_tool(
        customer_retention.CARD,
        "Customers lost, new and retained against the same dates one year earlier, for a period "
        "of one year or less. Use it for: are we keeping our customers?",
        {"start": START, "end": END, "store": STORE},
    ),
    function_tool(
        average_basket.CARD,
        "Average basket, the sales per order, over a period. Use it for: average order value, "
        "how much does an order bring in?",
        {"start": START, "end": END, "store": STORE},
    ),
    function_tool(
        target_attainment.CARD,
        "Sales against the targets of the file, by month and store. Use it for: are we hitting "
        "our targets?",
        {"start": START, "end": END, "store": STORE},
    ),
    function_tool(
        market_comparison.CARD,
        "Growth of the business compared with retail trade in its province (Statistics Canada), "
        "on the same months. Use it for: are we doing better than the market? The province is "
        "the one of the session.",
        {"start": START, "end": END, "store": STORE},
    ),
]


def on_session(metric):
    """A runner that calls a metric on the session data with the model's arguments."""
    return lambda data, **args: metric(data.df, data.roles, **args)


def attainment(data: Dataset, **args) -> dict:
    return target_attainment.target_attainment(data.df, data.roles, targets=data.targets, **args)


def compare_with_market(data: Dataset, **args) -> dict:
    if data.province is None or data.reference is None:
        return {"status": "error", "reason": "No market benchmark for this session"}
    return market_comparison.market_comparison(
        data.df, data.roles, province=data.province, reference=data.reference, **args
    )


# Each runner receives the session and the arguments chosen by the model. In strict mode the
# schema fixes their names; an unexpected one raises a TypeError, sent back as an error.
RUNNERS = {
    "sales_total": on_session(sales_total.sales_total),
    "sales_by_period": on_session(sales_by_period.sales_by_period),
    "sales_growth": on_session(sales_growth.sales_growth),
    "sales_ranking": on_session(sales_ranking.sales_ranking),
    "customer_retention": on_session(customer_retention.customer_retention),
    "average_basket": on_session(average_basket.average_basket),
    "target_attainment": attainment,
    "market_comparison": compare_with_market,
}


def run_tool(name: str, arguments: str, data: Dataset) -> dict:
    """Run the function the model asked for. A mistake goes back to the model as a result."""
    if name not in RUNNERS:
        return {"status": "error", "reason": f"Unknown tool: {name}"}
    try:
        return RUNNERS[name](data, **json.loads(arguments))
    except (KeyError, TypeError, ValueError) as error:
        return {"status": "error", "reason": f"{type(error).__name__}: {error}"}
