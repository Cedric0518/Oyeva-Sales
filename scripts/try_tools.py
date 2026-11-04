"""Ask the agent about Atlas, with the certified functions running here on the sample file.

Prints which tool answered (a certified function or Code Interpreter), its arguments, a short
result, and the answer. Run from the repository root, after `az login`:
    python -m scripts.try_tools "How much did we sell in 2025?" --runs 3
"""

import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from api.agent import ask
from api.checks.roles import read_targets, recognize_roles
from api.tools import Dataset

ATLAS = Path("evals/data/atlas/atlas_sales.xlsx")
STATCAN_ON = Path("tests/data/statcan_on_2026-10-23.json")


def atlas() -> Dataset:
    """The session the API would build after an upload of Atlas, region Ontario."""
    sheets = pd.read_excel(ATLAS, sheet_name=None, engine="openpyxl")
    orders = sheets.pop("Orders")
    roles = recognize_roles(orders, sheets)
    reference = json.loads(STATCAN_ON.read_text(encoding="utf-8"))
    return Dataset(orders, roles, read_targets(sheets, roles), "ON", reference)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the agent about Atlas, several times.")
    parser.add_argument("question")
    parser.add_argument("--runs", type=int, default=1)
    args = parser.parse_args()

    load_dotenv()
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential()
    )
    openai = project.get_openai_client()
    data = atlas()

    for run in range(1, args.runs + 1):
        start = time.perf_counter()
        answer = ask(openai, os.environ["AGENT_NAME"], args.question, data)
        seconds = time.perf_counter() - start
        tools = [name for name, *_ in answer.calls] + ["code_interpreter"] * len(answer.code)
        print(f"===== Run {run}: {', '.join(tools) or 'no tool'}, {seconds:.1f} s =====")
        for name, arguments, result in answer.calls:
            short = result.get("value", result.get("reason", ""))
            print(f"--- {name} {arguments} -> {result['status']} {short}")
        for code in answer.code:
            print("--- code_interpreter ---")
            print(code)
        if answer.stopped:
            print(f"--- stopped: {answer.stopped}")
        print("--- answer ---")
        print(answer.text)


if __name__ == "__main__":
    main()
