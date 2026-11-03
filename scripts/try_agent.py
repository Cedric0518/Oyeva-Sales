"""Ask the Foundry agent the same question several times, each time in a new conversation.

Prints the code that Code Interpreter actually ran, its output and the answer, to see which
definitions the agent chose. Run from the repository root, after `az login`:
    python scripts/try_agent.py "What was our average order value in 2025?" --runs 5
"""

import argparse
import json
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


def readable(arguments: str) -> str:
    """Return the code from tool call arguments, or the arguments themselves, indented."""
    try:
        parsed = json.loads(arguments)
    except json.JSONDecodeError:
        return arguments
    if isinstance(parsed, dict) and isinstance(parsed.get("code"), str):
        return parsed["code"]
    return json.dumps(parsed, indent=2)


def tool_calls(output_items) -> list[tuple[str, str, str]]:
    """List (tool, code or arguments, output) for each tool call in a response.

    Code Interpreter shows up as `code_interpreter_call` when attached directly to the agent,
    and as `mcp_call` when it comes from a toolbox, as with an agent built in the new portal.
    """
    calls = []
    for item in output_items:
        if item.type == "code_interpreter_call":
            calls.append(("code_interpreter", item.code or "", ""))
        elif item.type == "mcp_call":
            calls.append(
                (f"{item.server_label}/{item.name}", readable(item.arguments), item.output or "")
            )
    return calls


def ask(openai, agent_name: str, question: str) -> tuple[list[tuple[str, str, str]], str]:
    conversation = openai.conversations.create()
    response = openai.responses.create(
        conversation=conversation.id,
        input=question,
        extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
    )
    return tool_calls(response.output), response.output_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the agent the same question several times.")
    parser.add_argument("question")
    parser.add_argument("--runs", type=int, default=1)
    args = parser.parse_args()

    load_dotenv()
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential()
    )
    openai = project.get_openai_client()
    agent_name = os.environ["AGENT_NAME"]

    for run in range(1, args.runs + 1):
        calls, answer = ask(openai, agent_name, args.question)
        print(f"===== Run {run} =====")
        for tool, code, output in calls:
            print(f"--- tool call: {tool} ---")
            print(code)
            if output:
                print("--- tool output ---")
                print(output[:2000])
        print("--- answer ---")
        print(answer)


if __name__ == "__main__":
    main()
