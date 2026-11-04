"""The certified metrics as function tools: what the agent sees, and how the API runs them.

The model only chooses the arguments of a call (a period, and later a store). The data, the
column roles, the province and the Statistics Canada copy belong to the session: the API sets
them, never the model.
"""

import json
from dataclasses import dataclass

import pandas as pd

from api.metrics import sales_total


@dataclass
class Dataset:
    """What the API holds for the session. None of it is sent to the model."""

    df: pd.DataFrame
    roles: dict


START = {"type": "string", "description": "First day of the period, YYYY-MM-DD."}
END = {"type": "string", "description": "Last day of the period, YYYY-MM-DD, included."}


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
]

RUNNERS = {
    "sales_total": lambda data, args: sales_total.sales_total(
        data.df, data.roles, args["start"], args["end"]
    ),
}


def run_tool(name: str, arguments: str, data: Dataset) -> dict:
    """Run the function the model asked for. A mistake goes back to the model as a result."""
    if name not in RUNNERS:
        return {"status": "error", "reason": f"Unknown tool: {name}"}
    try:
        return RUNNERS[name](data, json.loads(arguments))
    except (KeyError, TypeError, ValueError) as error:
        return {"status": "error", "reason": f"{type(error).__name__}: {error}"}
