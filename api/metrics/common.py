"""Shared pieces of the certified metrics: the definition card, refusals, the period filter."""

from pathlib import Path

import pandas as pd
import yaml


def load_card(module_file: str) -> dict:
    """Read the YAML card that sits next to a metric's Python file."""
    path = Path(module_file).with_suffix(".yaml")
    card = yaml.safe_load(path.read_text(encoding="utf-8"))
    card["metric"] = {
        "name": card["name"],
        "version": card["version"],
        "definition": card["definition"],
    }
    return card


def missing_roles(needed: list[str], roles: dict) -> list[str]:
    return [role for role in needed if not roles.get(role)]


def refusal(card: dict, reason: str, **details) -> dict:
    return {"status": "refused", "reason": reason, **details, "metric": card["metric"]}


def in_period(df: pd.DataFrame, date_column: str, start: str, end: str) -> pd.DataFrame:
    """Rows dated from start to end, both days included (a time on the last day still counts)."""
    dates = pd.to_datetime(df[date_column])
    after_last = pd.Timestamp(end) + pd.Timedelta(days=1)
    return df[(dates >= pd.Timestamp(start)) & (dates < after_last)]
