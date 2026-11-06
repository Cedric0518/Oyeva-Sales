"""Create a new version of the agent: Code Interpreter and the certified metrics as functions.

The instructions come from api/agent_instructions.md and the function tools from api/tools.py,
so that each version can be traced to a commit. No file is attached: each request gives the
session file and its description through two structured inputs (docs/decisions/0011):
- sales_file_id: the Foundry file Code Interpreter mounts, the session rows as sales_data.csv;
- dataset: what the API read in the file, placed in the instructions.
Run from the repository root, after `az login`:
    python -m scripts.create_agent
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AutoCodeInterpreterToolParam,
    CodeInterpreterTool,
    FunctionTool,
    PromptAgentDefinition,
    StructuredInputDefinition,
)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from api.tools import TOOLS

INSTRUCTIONS = Path("api/agent_instructions.md")
STRUCTURED_INPUTS = {
    "sales_file_id": StructuredInputDefinition(
        description="Foundry file id of the session's sales rows, for Code Interpreter.",
        required=True,
        schema={"type": "string"},
    ),
    "dataset": StructuredInputDefinition(
        description="What the API read in the session's sales file: rows, dates, columns.",
        required=True,
        schema={"type": "string"},
    ),
}


def main() -> None:
    load_dotenv()
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential()
    )
    code_interpreter = CodeInterpreterTool(
        container=AutoCodeInterpreterToolParam(file_ids=["{{sales_file_id}}"])
    )
    functions = [FunctionTool(tool) for tool in TOOLS]
    agent = project.agents.create_version(
        agent_name=os.environ["AGENT_NAME"],
        definition=PromptAgentDefinition(
            model=os.environ["AGENT_MODEL"],
            instructions=INSTRUCTIONS.read_text(encoding="utf-8"),
            tools=[code_interpreter, *functions],
            structured_inputs=STRUCTURED_INPUTS,
        ),
        description="Code Interpreter on the session file and the 8 certified metrics.",
    )
    print(f"Agent {agent.name} version {agent.version}, model {os.environ['AGENT_MODEL']}")
    print("Structured inputs: " + ", ".join(STRUCTURED_INPUTS))
    print("Tools: code_interpreter, " + ", ".join(tool["name"] for tool in TOOLS))


if __name__ == "__main__":
    main()
