"""B4 mini-measure: does the agent call the certified function when one covers the question?

Asks each question 3 times about Atlas and writes a report in evals/results/. The reading rule
was written in issue #14 before the results. Commit first, then run from the repository root,
after `az login`:
    python -m evals.tool_choice --label v1
"""

import argparse
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from api.agent import ask
from scripts.try_tools import atlas

RUNS = 3
CODE = "code_interpreter"
RESULTS = Path("evals/results")

# (id, question, expected certified function); None for a control: no certified function.
CASES = [
    ("1", "How much did we sell in 2025?", "sales_total"),
    ("2", "Show our monthly sales for 2025.", "sales_by_period"),
    (
        "3",
        "Compared with the same months of 2025, how did our sales change from January to "
        "August 2026?",
        "sales_growth",
    ),
    ("4", "Who were our top 10 customers in 2025?", "sales_ranking"),
    ("5", "What were our 5 best-selling products in 2025?", "sales_ranking"),
    (
        "6",
        "How many customers did we lose from January-August 2025 to January-August 2026?",
        "customer_retention",
    ),
    ("7", "What was our average order value in 2025?", "average_basket"),
    ("8", "Did we hit our sales targets in 2025?", "target_attainment"),
    (
        "9",
        "Are we doing better than the Ontario retail market from January to August 2026?",
        "market_comparison",
    ),
    ("10", "How much did the Toronto - Queen Street store sell in March 2025?", "sales_by_period"),
    ("C1", "Which day of the week had the highest sales in 2025?", None),
    ("C2", "What was our profit margin in 2025?", None),
]


def succeeded(expected: str | None, tools: list[str]) -> bool:
    """A certified question needs its function and no Code Interpreter; a control, no function."""
    functions = [tool for tool in tools if tool != CODE]
    if expected is None:
        return not functions
    return expected in functions and CODE not in tools


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure the tool choice of the agent.")
    parser.add_argument("--label", default="v1", help="name of the report, e.g. v1")
    args = parser.parse_args()

    load_dotenv()
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential()
    )
    openai = project.get_openai_client()
    agent_name = os.environ["AGENT_NAME"]
    latest = next(iter(project.agents.list_versions(agent_name=agent_name, order="desc")))
    data = atlas()

    runs = []
    for case, question, expected in CASES:
        for run in range(1, RUNS + 1):
            start = time.perf_counter()
            answer = ask(openai, agent_name, question, data)
            seconds = round(time.perf_counter() - start, 1)
            tools = [name for name, *_ in answer.calls] + [CODE] * len(answer.code)
            ok = succeeded(expected, tools)
            print(f"{case:>3} run {run}: {'ok' if ok else 'NO'}  {', '.join(tools) or 'no tool'}")
            runs.append(
                {
                    "case": case,
                    "run": run,
                    "question": question,
                    "expected": expected,
                    "tools": tools,
                    "succeeded": ok,
                    "calls": [[name, arguments] for name, arguments, _ in answer.calls],
                    "code": answer.code,
                    "stopped": answer.stopped,
                    "seconds": seconds,
                    "answer": answer.text,
                }
            )

    certified = [run for run in runs if run["expected"]]
    total = sum(run["succeeded"] for run in certified)
    report = {
        "label": args.label,
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
        "commit": git("rev-parse", "--short", "HEAD"),
        "uncommitted_changes": bool(git("status", "--porcelain")),
        "agent": agent_name,
        "agent_version": latest.version,
        "model": os.environ["AGENT_MODEL"],
        "runs_per_question": RUNS,
        "certified_runs_with_expected_function": f"{total}/{len(certified)}",
        "runs": runs,
    }
    path = RESULTS / f"b4-tool-choice-{args.label}.json"
    path.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print()
    for case, _, _ in CASES:
        mine = [run for run in runs if run["case"] == case]
        print(f"{case:>3}: {sum(run['succeeded'] for run in mine)}/{RUNS}")
    print(f"\nCertified questions: {total}/{len(certified)} runs with the expected function")
    print(f"Agent version {latest.version}, commit {report['commit']}")
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
