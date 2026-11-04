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


def check_inputs(
    card: dict, df: pd.DataFrame, roles: dict, store: str | None = None, extra: tuple = ()
) -> dict | None:
    """A refusal if a column the metric needs is missing or the store is unknown, else None."""
    needed = card["requires"] + list(extra) + (["region"] if store else [])
    missing = missing_roles(needed, roles)
    if missing:
        return refusal(
            card, "The file has no column for: " + ", ".join(missing), missing_roles=missing
        )
    if store:
        stores = sorted(df[roles["region"]].dropna().unique().tolist())
        if store not in stores:
            return refusal(card, f"Unknown store: {store}", stores=stores)
    return None


def in_period(df: pd.DataFrame, date_column: str, start: str, end: str) -> pd.DataFrame:
    """Rows dated from start to end, both days included (a time on the last day still counts)."""
    dates = pd.to_datetime(df[date_column])
    after_last = pd.Timestamp(end) + pd.Timedelta(days=1)
    return df[(dates >= pd.Timestamp(start)) & (dates < after_last)]


# Customer names that stand for "no identified customer", compared on letters and digits only.
PLACEHOLDER_CUSTOMERS = {
    "walkin",
    "walkincustomer",
    "cashcustomer",
    "cashsale",
    "guest",
    "anonymous",
    "unknown",
    "na",
    "none",
}


def is_placeholder(name) -> bool:
    """True for an empty customer name or a name like "Walk-in" that is not a real customer."""
    if pd.isna(name):
        return True
    key = "".join(ch for ch in str(name).lower() if ch.isalnum())
    return not key or key in PLACEHOLDER_CUSTOMERS
