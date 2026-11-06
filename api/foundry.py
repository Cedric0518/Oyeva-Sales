"""The Foundry client of the API, and the session files given to Code Interpreter.

No key: DefaultAzureCredential uses `az login` locally and the managed identity in Azure
(docs/decisions/0005). The client is created on first use, so that the API starts and its
tests run without Azure.
"""

import os
import threading

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from api.reading import SESSION_FILE, ReadFile


def upload_session_file(openai, content: bytes) -> str:
    """Upload the sales rows for Code Interpreter; the container sees them as SESSION_FILE."""
    return openai.files.create(file=(SESSION_FILE, content), purpose="assistants").id


class Foundry:
    def __init__(self):
        self._client = None
        self._files: dict[str, str] = {}  # dataset id -> Foundry file id
        self._lock = threading.Lock()

    @property
    def agent_name(self) -> str:
        return os.environ["AGENT_NAME"]

    def client(self):
        with self._lock:
            if self._client is None:
                project = AIProjectClient(
                    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
                    credential=DefaultAzureCredential(),
                )
                openai = project.get_openai_client()
                # One Foundry request waits at most this long (default 90 s), with one retry.
                seconds = float(os.environ.get("AGENT_REQUEST_SECONDS", "90"))
                self._client = openai.with_options(timeout=seconds, max_retries=1)
            return self._client

    def file_id(self, read: ReadFile) -> str:
        """The Foundry file of a dataset, uploaded the first time a question is asked about it.
        The same file content in two sessions is uploaded once."""
        dataset_id = read.response["dataset_id"]
        with self._lock:
            if dataset_id in self._files:
                return self._files[dataset_id]
        file_id = upload_session_file(self.client(), read.csv)
        with self._lock:
            self._files[dataset_id] = file_id
        return file_id
