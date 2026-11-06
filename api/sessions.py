"""What the API keeps for each browser session, in memory (B6 moves the files to Blob Storage).

A session is the X-Session-Id of a browser tab. It holds its uploaded files, its conversations,
and whether an answer is being written: one answer at a time per session.
"""

import threading
import time
from dataclasses import dataclass, field

from api.reading import ReadFile

MAX_SESSIONS = 50  # the least recently used session is dropped beyond this
MAX_DATASETS = 2  # files kept per session; the oldest is dropped beyond this
BUSY_SECONDS = 240  # an answer older than this no longer blocks the session


@dataclass
class Session:
    datasets: dict[str, ReadFile] = field(default_factory=dict)
    conversations: dict[str, str] = field(default_factory=dict)  # conversation id -> dataset id
    broken: set[str] = field(default_factory=set)  # conversations to replace by a new one
    busy_since: float | None = None
    seen: float = field(default_factory=time.monotonic)


class Sessions:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def _get(self, session_id: str) -> Session:
        session = self._sessions.get(session_id)
        if session is None:
            if len(self._sessions) >= MAX_SESSIONS:
                oldest = min(self._sessions, key=lambda key: self._sessions[key].seen)
                del self._sessions[oldest]
            session = self._sessions[session_id] = Session()
        session.seen = time.monotonic()
        return session

    def add_dataset(self, session_id: str, read: ReadFile) -> None:
        with self._lock:
            datasets = self._get(session_id).datasets
            datasets.pop(read.response["dataset_id"], None)
            datasets[read.response["dataset_id"]] = read
            while len(datasets) > MAX_DATASETS:
                del datasets[next(iter(datasets))]

    def dataset(self, session_id: str, dataset_id: str) -> ReadFile | None:
        with self._lock:
            return self._get(session_id).datasets.get(dataset_id)

    def begin(self, session_id: str) -> bool:
        """Mark the session busy. False if an answer is already being written."""
        with self._lock:
            session = self._get(session_id)
            now = time.monotonic()
            if session.busy_since is not None and now - session.busy_since < BUSY_SECONDS:
                return False
            session.busy_since = now
            return True

    def end(self, session_id: str) -> None:
        with self._lock:
            self._get(session_id).busy_since = None

    def conversation(
        self, session_id: str, conversation_id: str | None, dataset_id: str
    ) -> str | None:
        """The conversation to continue, or None to start a new one: an unknown conversation,
        one about another file, or one that ended with an error is not continued."""
        with self._lock:
            session = self._get(session_id)
            if conversation_id in session.broken:
                return None
            if session.conversations.get(conversation_id) != dataset_id:
                return None
            return conversation_id

    def remember(self, session_id: str, conversation_id: str, dataset_id: str) -> None:
        with self._lock:
            self._get(session_id).conversations[conversation_id] = dataset_id

    def break_off(self, session_id: str, conversation_id: str | None) -> None:
        if conversation_id:
            with self._lock:
                self._get(session_id).broken.add(conversation_id)
