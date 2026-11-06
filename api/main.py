"""The Oyeva Sales API: the routes of docs/contract.md.

Run locally from the repository root, after `az login`:
    uvicorn api.main:app --reload
"""

import json
import logging
import os
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException

from api.agent import UNAVAILABLE, turn
from api.foundry import Foundry
from api.market.statcan import PROVINCES
from api.reading import ReadError, ReadFile, read_sales_file
from api.sessions import Sessions

load_dotenv()
logger = logging.getLogger("oyeva.api")

MAX_FILE_BYTES = 20 * 1024 * 1024
SAMPLE = Path("evals/data/atlas/atlas_sales.xlsx")
# Statistics Canada copy until B6 reads the latest one from Blob Storage. The committed test
# copy covers Ontario only: another province gets a refusal that names the provinces covered.
REFERENCE = Path(os.environ.get("STATCAN_REFERENCE", "tests/data/statcan_on_2026-10-23.json"))
STATUS = {
    "unsupported_format": 415,
    "file_too_large": 413,
    "unreadable_file": 422,
    "invalid_request": 422,
    "missing_session": 400,
    "dataset_not_found": 404,
    "rate_limited": 429,
    "internal": 500,
}


class ApiError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


def error_response(code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=STATUS[code])


app = FastAPI(title="Oyeva Sales API", version="0.5.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Session-Id"],
)


@app.exception_handler(ApiError)
def api_error(_: Request, error: ApiError) -> JSONResponse:
    return error_response(error.code, error.message)


@app.exception_handler(RequestValidationError)
def invalid_request(_: Request, error: RequestValidationError) -> JSONResponse:
    first = error.errors()[0]
    where = ".".join(str(part) for part in first["loc"] if part not in ("body", "query"))
    return error_response("invalid_request", f"{where}: {first['msg']}")


@app.exception_handler(HTTPException)
def http_error(_: Request, error: HTTPException) -> JSONResponse:
    response = error_response("invalid_request", str(error.detail))
    response.status_code = error.status_code
    return response


@app.exception_handler(Exception)
def internal(_: Request, error: Exception) -> JSONResponse:
    logger.exception("Unexpected error", exc_info=error)
    return error_response("internal", "Something went wrong on our side. Try again.")


# ---------- what the routes share: overridden in the tests ----------

_sessions, _foundry = Sessions(), Foundry()


def get_sessions() -> Sessions:
    return _sessions


def get_foundry() -> Foundry:
    return _foundry


@lru_cache
def get_reference() -> dict | None:
    if not REFERENCE.exists():
        logger.warning("No Statistics Canada copy at %s: no market comparison", REFERENCE)
        return None
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


def session_id(x_session_id: Annotated[str | None, Header()] = None) -> str:
    try:
        return str(uuid.UUID(x_session_id))
    except (AttributeError, TypeError, ValueError):
        message = "The X-Session-Id header is missing or is not a valid UUID. Reload the page."
        raise ApiError("missing_session", message) from None


SessionId = Annotated[str, Depends(session_id)]
SessionStore = Annotated[Sessions, Depends(get_sessions)]


def read_or_fail(content: bytes, file_name: str, region: str) -> ReadFile:
    try:
        return read_sales_file(content, file_name, region, get_reference())
    except ReadError as error:
        raise ApiError(error.code, error.message) from error


@lru_cache
def sample() -> ReadFile:
    """Atlas, read once: every session that asks for the sample shares the same read file."""
    return read_or_fail(SAMPLE.read_bytes(), SAMPLE.name, "ON")


# ---------- routes ----------


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/upload")
def upload(
    session: SessionId,
    sessions: SessionStore,
    file: Annotated[UploadFile, File()],
    region: Annotated[str, Form()],
    context: Annotated[UploadFile | None, File()] = None,
) -> dict:
    if region not in PROVINCES:
        raise ApiError("invalid_request", f"Unknown province code: {region}")
    content = file.file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise ApiError("file_too_large", "The sales file is larger than 20 MB.")
    if context is not None:
        logger.info("Context document %s not read yet (B9)", context.filename)
    read = read_or_fail(content, file.filename or "sales.csv", region)
    sessions.add_dataset(session, read)
    return read.response


class SampleRequest(BaseModel):
    sample: str


@app.post("/api/sample")
def load_sample(request: SampleRequest, session: SessionId, sessions: SessionStore) -> dict:
    if request.sample != "atlas":
        raise ApiError("invalid_request", f"Unknown sample: {request.sample}")
    read = sample()
    sessions.add_dataset(session, read)
    return read.response


class ChatRequest(BaseModel):
    dataset_id: str
    conversation_id: str | None = None
    message: str = Field(min_length=1, max_length=4000)


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/chat")
def chat(
    request: ChatRequest,
    session: SessionId,
    sessions: SessionStore,
    foundry: Annotated[Foundry, Depends(get_foundry)],
) -> StreamingResponse:
    read = sessions.dataset(session, request.dataset_id)
    if read is None:
        message = "This file is no longer in your session. Upload it again."
        raise ApiError("dataset_not_found", message)
    if not sessions.begin(session):
        raise ApiError("rate_limited", "Wait for the current answer to finish.")
    continued = sessions.conversation(session, request.conversation_id, request.dataset_id)

    def events():
        conversation, started = continued, False
        message_id = "msg_" + uuid.uuid4().hex[:8]
        try:
            openai = foundry.client()
            inputs = {"sales_file_id": foundry.file_id(read), "dataset": read.description}
            if conversation is None:
                conversation = openai.conversations.create().id
            sessions.remember(session, conversation, request.dataset_id)
            yield sse("start", {"conversation_id": conversation, "message_id": message_id})
            started = True
            for event, data in turn(
                openai, foundry.agent_name, conversation, request.message, read.data, inputs
            ):
                if event == "error":
                    sessions.break_off(session, conversation)
                yield sse(event, data)
        except Exception:
            logger.exception("Chat failed")
            sessions.break_off(session, conversation)
            if not started:
                yield sse("start", {"conversation_id": conversation, "message_id": message_id})
            yield sse("error", {"code": "internal", "message": UNAVAILABLE})
        finally:
            sessions.end(session)

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(events(), media_type="text/event-stream", headers=headers)
