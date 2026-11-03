"""Create a new version of the agent, with Code Interpreter attached directly (no toolbox).

The instructions come from api/agent_instructions.md, so that each version can be traced to a
commit. The sample sales file is uploaded once, then reused. Run from the repository root, after
`az login`:
    python scripts/create_agent.py
"""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AutoCodeInterpreterToolParam,
    CodeInterpreterTool,
    PromptAgentDefinition,
)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

INSTRUCTIONS = Path("api/agent_instructions.md")
SAMPLE = Path("evals/data/atlas/atlas_sales.xlsx")


def sample_file_id(openai) -> str:
    """Return the id of the uploaded sample file, uploading it the first time."""
    for file in openai.files.list(purpose="assistants"):
        if file.filename == SAMPLE.name:
            return file.id
    with SAMPLE.open("rb") as handle:
        return openai.files.create(file=handle, purpose="assistants").id


def main() -> None:
    load_dotenv()
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential()
    )
    openai = project.get_openai_client()
    file_id = sample_file_id(openai)
    code_interpreter = CodeInterpreterTool(
        container=AutoCodeInterpreterToolParam(file_ids=[file_id])
    )
    agent = project.agents.create_version(
        agent_name=os.environ["AGENT_NAME"],
        definition=PromptAgentDefinition(
            model=os.environ["AGENT_MODEL"],
            instructions=INSTRUCTIONS.read_text(encoding="utf-8"),
            tools=[code_interpreter],
        ),
        description="Code Interpreter attached directly, sample file atlas_sales.xlsx.",
    )
    print(f"Agent {agent.name} version {agent.version}, model {os.environ['AGENT_MODEL']}")
    print(f"Sample file {file_id}")


if __name__ == "__main__":
    main()
