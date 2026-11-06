"""Ask the agent about Atlas, with the certified functions running here on the sample file.

Atlas is read by the same code as an upload to the API, and its rows are given to Code
Interpreter through the agent's structured inputs, as in a session.

Prints which tool answered (a certified function or Code Interpreter), its arguments, a short
result, and the answer. Run from the repository root, after `az login`:
    python -m scripts.try_tools "How much did we sell in 2025?" --runs 3
"""

import argparse
import json
import os
import time
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from api.agent import ask
from api.foundry import upload_session_file
from api.reading import ReadFile, read_sales_file

ATLAS = Path("evals/data/atlas/atlas_sales.xlsx")
STATCAN_ON = Path("tests/data/statcan_on_2026-10-23.json")


def atlas() -> ReadFile:
    """Atlas read exactly as the API reads an upload, region Ontario."""
    reference = json.loads(STATCAN_ON.read_text(encoding="utf-8"))
    return read_sales_file(ATLAS.read_bytes(), ATLAS.name, "ON", reference)


def session_inputs(openai, read: ReadFile) -> dict:
    """The structured inputs of the agent for this file; the rows are uploaded once per run."""
    return {"sales_file_id": upload_session_file(openai, read.csv), "dataset": read.description}


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
    read = atlas()
    inputs = session_inputs(openai, read)

    for run in range(1, args.runs + 1):
        start = time.perf_counter()
        answer = ask(openai, os.environ["AGENT_NAME"], args.question, read.data, inputs)
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
