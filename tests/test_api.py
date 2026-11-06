"""The routes of docs/contract.md, with a fake Foundry: no Azure needed."""

import json
import uuid
from types import SimpleNamespace as Item

import pytest
from fastapi.testclient import TestClient

import api.main as main
from api.sessions import Sessions
from tests.test_agent import FakeOpenAI, function_call, response

SALES = "order_date,store,amount\n2025-01-02,North,100.00\n2025-02-03,South,50.50\n"


class FakeFoundry:
    agent_name = "oyeva-sales-agent"

    def __init__(self, *scripted):
        self.openai = FakeOpenAI(*scripted)
        self.uploaded = []

    def client(self):
        return self.openai

    def file_id(self, read):
        self.uploaded.append(read.response["dataset_id"])
        return "file-session"


@pytest.fixture
def api():
    """A client, its session header, and the fake Foundry the next test scripts."""
    sessions = Sessions()
    main.app.dependency_overrides[main.get_sessions] = lambda: sessions
    foundry = FakeFoundry()
    main.app.dependency_overrides[main.get_foundry] = lambda: foundry
    client = TestClient(main.app)
    headers = {"X-Session-Id": str(uuid.uuid4())}
    yield client, headers, foundry
    main.app.dependency_overrides.clear()


def upload(client, headers, text=SALES, name="sales.csv", region="ON"):
    files = {"file": (name, text.encode(), "text/csv")}
    return client.post("/api/upload", headers=headers, files=files, data={"region": region})


def events(body: str) -> list[tuple[str, dict]]:
    parsed = []
    for block in body.strip().split("\n\n"):
        event, data = block.split("\n")
        parsed.append((event.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return parsed


def test_health(api):
    client, _, _ = api
    assert client.get("/api/health").json() == {"status": "ok"}


@pytest.mark.parametrize("header", [None, "not-a-uuid"])
def test_a_missing_or_invalid_session_is_refused(api, header):
    client, _, _ = api
    headers = {"X-Session-Id": header} if header else {}
    reply = upload(client, headers)
    assert reply.status_code == 400
    assert reply.json()["error"]["code"] == "missing_session"


def test_upload_returns_the_report_of_the_file(api):
    client, headers, _ = api
    reply = upload(client, headers)
    assert reply.status_code == 200
    body = reply.json()
    assert body["rows"] == 2
    assert body["roles"]["date"] == "order_date"
    assert body["roles"]["region"] == "store"
    assert body["context"] is None
    assert [c["id"] for c in body["checks"]][:2] == ["roles", "duplicates"]


@pytest.mark.parametrize(
    ("name", "region", "status", "code"),
    [
        ("notes.pdf", "ON", 415, "unsupported_format"),
        ("sales.csv", "XX", 422, "invalid_request"),
        ("sales.xlsx", "ON", 422, "unreadable_file"),
    ],
)
def test_upload_errors_follow_the_contract(api, name, region, status, code):
    client, headers, _ = api
    reply = upload(client, headers, name=name, region=region)
    assert reply.status_code == status
    assert reply.json()["error"]["code"] == code
    assert reply.json()["error"]["message"]


def test_a_file_over_the_limit_is_refused(api, monkeypatch):
    client, headers, _ = api
    monkeypatch.setattr(main, "MAX_FILE_BYTES", 10)
    reply = upload(client, headers)
    assert reply.status_code == 413
    assert reply.json()["error"]["code"] == "file_too_large"


def test_a_missing_field_is_an_invalid_request(api):
    client, headers, _ = api
    reply = client.post("/api/upload", headers=headers, data={"region": "ON"})
    assert reply.status_code == 422
    assert reply.json()["error"]["code"] == "invalid_request"


def test_the_sample_is_atlas(api):
    client, headers, _ = api
    reply = client.post("/api/sample", headers=headers, json={"sample": "atlas"})
    assert reply.status_code == 200
    assert reply.json()["file_name"] == "atlas_sales.xlsx"
    assert reply.json()["rows"] == 59764
    unknown = client.post("/api/sample", headers=headers, json={"sample": "other"})
    assert unknown.json()["error"]["code"] == "invalid_request"


def test_chat_about_a_dataset_of_another_session_is_not_found(api):
    client, headers, _ = api
    dataset_id = upload(client, headers).json()["dataset_id"]
    other = {"X-Session-Id": str(uuid.uuid4())}
    reply = client.post(
        "/api/chat", headers=other, json={"dataset_id": dataset_id, "message": "Hi"}
    )
    assert reply.status_code == 404
    assert reply.json()["error"]["code"] == "dataset_not_found"


def test_chat_streams_the_events_of_the_contract(api):
    client, headers, foundry = api
    foundry.openai.scripted = [
        response("r1", function_call("sales_total", start="2025-01-01", end="2025-12-31")),
        response("r2", text="You sold $150.50 in 2025."),
    ]
    dataset_id = upload(client, headers).json()["dataset_id"]
    question = {"dataset_id": dataset_id, "conversation_id": None, "message": "2025 sales?"}
    reply = client.post("/api/chat", headers=headers, json=question)
    assert reply.status_code == 200
    assert reply.headers["content-type"].startswith("text/event-stream")
    stream = events(reply.text)
    assert [event for event, _ in stream] == ["start", "step", "step", "text", "done"]
    assert stream[0][1]["conversation_id"] == "conv_1"
    assert stream[0][1]["message_id"].startswith("msg_")
    assert stream[3][1] == {"delta": "You sold $150.50 in 2025."}
    sent = foundry.openai.sent[0]
    assert sent["extra_body"]["structured_inputs"]["sales_file_id"] == "file-session"
    assert "order_date" in sent["extra_body"]["structured_inputs"]["dataset"]
    assert foundry.uploaded == [dataset_id]


def test_the_next_message_continues_the_conversation(api):
    client, headers, foundry = api
    foundry.openai.scripted = [response("r1", text="First."), response("r2", text="Second.")]
    foundry.openai.conversations = Item(create=lambda: Item(id=f"conv_{uuid.uuid4().hex[:4]}"))
    dataset_id = upload(client, headers).json()["dataset_id"]
    first = events(
        client.post(
            "/api/chat", headers=headers, json={"dataset_id": dataset_id, "message": "One"}
        ).text
    )
    conversation = first[0][1]["conversation_id"]
    question = {"dataset_id": dataset_id, "conversation_id": conversation, "message": "Two"}
    second = events(client.post("/api/chat", headers=headers, json=question).text)
    assert second[0][1]["conversation_id"] == conversation
    assert foundry.openai.sent[1]["conversation"] == conversation


def test_after_an_error_the_next_message_starts_a_new_conversation(api):
    client, headers, foundry = api
    ids = iter(["conv_a", "conv_b"])
    foundry.openai.conversations = Item(create=lambda: Item(id=next(ids)))
    foundry.openai.scripted = [RuntimeError("Foundry is down"), response("r2", text="Back.")]
    dataset_id = upload(client, headers).json()["dataset_id"]
    first = events(
        client.post(
            "/api/chat", headers=headers, json={"dataset_id": dataset_id, "message": "One"}
        ).text
    )
    assert [event for event, _ in first] == ["start", "error"]
    question = {"dataset_id": dataset_id, "conversation_id": "conv_a", "message": "Two"}
    second = events(client.post("/api/chat", headers=headers, json=question).text)
    assert second[0][1]["conversation_id"] == "conv_b"
    assert second[-1] == ("done", {})


def test_one_answer_at_a_time_per_session(api):
    client, headers, _ = api
    dataset_id = upload(client, headers).json()["dataset_id"]
    sessions = main.app.dependency_overrides[main.get_sessions]()
    assert sessions.begin(headers["X-Session-Id"])
    reply = client.post(
        "/api/chat", headers=headers, json={"dataset_id": dataset_id, "message": "Hi"}
    )
    assert reply.status_code == 429
    assert reply.json()["error"]["code"] == "rate_limited"
