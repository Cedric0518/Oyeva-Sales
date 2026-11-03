"""Check that the signed-in identity reaches each Azure service of Oyeva Sales, without any key.

Run from the repository root, after `az login`:
    python scripts/check_access.py
"""

import logging
import os
import sys

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

EXPECTED_CONTAINERS = {"uploads", "outputs", "reference"}


def check_storage(credential) -> str:
    client = BlobServiceClient(account_url=os.environ["STORAGE_ACCOUNT_URL"], credential=credential)
    names = {container.name for container in client.list_containers()}
    missing = EXPECTED_CONTAINERS - names
    if missing:
        raise RuntimeError(f"missing containers: {sorted(missing)}")
    return f"containers {sorted(names)}"


def check_search(credential) -> str:
    client = SearchIndexClient(endpoint=os.environ["SEARCH_ENDPOINT"], credential=credential)
    names = list(client.list_index_names())
    return f"{len(names)} index(es) {names}"


def check_foundry(credential) -> str:
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=credential
    )
    names = sorted(deployment.name for deployment in project.deployments.list())
    model = os.environ["AGENT_MODEL"]
    if model not in names:
        raise RuntimeError(f"AGENT_MODEL={model} is not deployed; deployments: {names}")
    return f"deployments {names}"


CHECKS = [
    ("Blob Storage", check_storage),
    ("AI Search", check_search),
    ("Foundry project", check_foundry),
]


def main() -> int:
    load_dotenv()
    logging.getLogger("azure").setLevel(logging.ERROR)  # keep the output to one line per service
    credential = DefaultAzureCredential()
    failures = 0
    for name, check in CHECKS:
        try:
            print(f"OK    {name}: {check(credential)}")
        except Exception as exc:  # report every failure, then move on to the next service
            failures += 1
            first_line = str(exc).splitlines()[0] if str(exc) else ""
            print(f"FAIL  {name}: {type(exc).__name__}: {first_line}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
