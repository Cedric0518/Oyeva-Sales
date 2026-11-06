"""The agent loop: one user message is one turn, in a Foundry conversation.

Foundry runs the model and Code Interpreter; Code Interpreter works on the session file, given
at each request through the structured inputs of the agent (docs/decisions/0011). The certified
functions run here, on the session data: the agent only receives their results. A turn yields
the events of docs/contract.md, section 7, after `start`, and ends with `done` or `error`.
"""

import json
import time
from collections.abc import Iterator
from dataclasses import dataclass, field

from openai import APIConnectionError, APIStatusError, APITimeoutError

from api.tools import METRICS, Dataset, run_tool

MAX_ROUNDS = 5  # responses that may call functions; the next one must answer in words
TURN_SECONDS = 180  # a turn that takes longer stops with an error
BLOCKED = "This request was blocked by the safety system."
TOO_LONG = "The assistant took too long to answer. Try a narrower question."
UNAVAILABLE = "The assistant is not available right now. Try again in a moment."
LABELS = {
    "sales_total": "Sales total",
    "sales_by_period": "Sales by period",
    "sales_growth": "Sales growth",
    "sales_ranking": "Ranking",
    "customer_retention": "Customer retention",
    "average_basket": "Average basket",
    "target_attainment": "Sales against targets",
    "market_comparison": "Comparison with provincial retail",
}

Event = tuple[str, dict]


@dataclass
class Answer:
    """What a turn did, for the trial scripts and the measures."""

    text: str = ""
    calls: list = field(default_factory=list)  # (tool, arguments, result) for each function call
    code: list = field(default_factory=list)  # the code that Code Interpreter ran
    stopped: str | None = None  # why the agent had to answer without more function calls


class Ids:
    """Event ids of one answer: s1, s2... for steps, c1... for charts, t1... for tables."""

    def __init__(self):
        self.counts = {}

    def next(self, prefix: str) -> str:
        self.counts[prefix] = self.counts.get(prefix, 0) + 1
        return f"{prefix}{self.counts[prefix]}"


def of_type(response, kind: str) -> list:
    return [item for item in response.output if item.type == kind]


def agent_body(agent_name: str, inputs: dict) -> dict:
    """The agent to run and the session values of its structured inputs."""
    return {
        "agent_reference": {"name": agent_name, "type": "agent_reference"},
        "structured_inputs": inputs,
    }


def label(name: str, arguments: str) -> str:
    """The step label shown to the user: "Sales total, 2025-01-01 to 2025-12-31, Ottawa"."""
    try:
        args = json.loads(arguments)
    except ValueError:
        args = {}
    parts = [LABELS.get(name, name)]
    if args.get("start") and args.get("end"):
        parts.append(f"{args['start']} to {args['end']}")
    if args.get("by"):
        parts.append(f"by {args['by']}")
    if args.get("store"):
        parts.append(str(args["store"]))
    return ", ".join(parts)


def result_events(name: str, result: dict, ids: Ids) -> list[Event]:
    """The chart and the table of a certified result, with their provenance."""
    if result.get("status") != "ok":
        return []
    if name == "market_comparison":
        provenance = "market"
        extra = {key: result[key] for key in ("benchmark", "source", "published")}
    else:
        provenance, extra = "certified", {"metric": result["metric"]}
    events = []
    if "chart" in result:
        chart = {"id": ids.next("c"), "provenance": provenance, "chart": result["chart"], **extra}
        events.append(("chart", chart))
    if "table" in result:
        table = {"id": ids.next("t"), "provenance": provenance, **result["table"], **extra}
        events.append(("table", table))
    return events


def blocked(error: APIStatusError) -> bool:
    """True when the guardrail refused the request (content filter)."""
    return error.status_code == 400 and "content_filter" in str(error).lower()


def turn(
    openai,
    agent_name: str,
    conversation_id: str,
    message: str,
    data: Dataset,
    inputs: dict,
    answer: Answer | None = None,
    seconds: float = TURN_SECONDS,
) -> Iterator[Event]:
    """Answer one message. Function results always go back to the conversation, so that the
    next message finds no call left without an output."""
    answer = answer if answer is not None else Answer()
    deadline = time.monotonic() + seconds
    body = agent_body(agent_name, inputs)
    ids, failed = Ids(), set()
    request = {"input": message}
    try:
        for round_ in range(MAX_ROUNDS + 1):
            if time.monotonic() > deadline:
                answer.stopped = TOO_LONG
                yield "error", {"code": "internal", "message": TOO_LONG}
                return
            response = openai.responses.create(
                conversation=conversation_id, extra_body=body, **request
            )
            if getattr(response, "error", None):
                answer.stopped = f"Foundry error: {response.error}"
                yield "error", {"code": "internal", "message": UNAVAILABLE}
                return
            for item in of_type(response, "code_interpreter_call"):
                code = item.code or ""
                answer.code.append(code)
                step = {"id": ids.next("s"), "tool": "code", "label": "Code Interpreter"}
                yield "step", {**step, "status": "done", "code": code}
            requests = of_type(response, "function_call")
            if not requests:
                answer.text = response.output_text or ""
                if answer.text:
                    yield "text", {"delta": answer.text}
                yield "done", {}
                return

            outputs = []
            for item in requests:
                tool = "market" if item.name == "market_comparison" else "certified"
                step = {
                    "id": ids.next("s"),
                    "tool": tool,
                    "label": label(item.name, item.arguments),
                }
                if item.name in METRICS:
                    step["metric"] = METRICS[item.name]
                yield "step", {**step, "status": "running"}
                result = run_tool(item.name, item.arguments, data)
                answer.calls.append((item.name, item.arguments, result))
                status = "failed" if result["status"] == "error" else "done"
                yield "step", {**step, "status": status}
                yield from result_events(item.name, result, ids)
                if result["status"] == "error":
                    if (item.name, item.arguments) in failed:
                        answer.stopped = f"The same call failed twice: {item.name} {item.arguments}"
                    failed.add((item.name, item.arguments))
                outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(result),
                    }
                )
            request = {"input": outputs}
            if round_ + 1 == MAX_ROUNDS and not answer.stopped:
                answer.stopped = f"No final answer after {MAX_ROUNDS} rounds of function calls"
            if answer.stopped:
                request["tool_choice"] = "none"  # the results go back, and the agent answers
        # Still calling functions after being told to answer: the turn ends with an error.
        yield "error", {"code": "internal", "message": UNAVAILABLE}
    except APITimeoutError:
        answer.stopped = TOO_LONG
        yield "error", {"code": "internal", "message": TOO_LONG}
    except APIStatusError as error:
        if blocked(error):
            answer.stopped = BLOCKED
            yield "blocked", {"message": BLOCKED}
            yield "done", {}
        else:
            answer.stopped = f"Foundry error {error.status_code}: {error}"
            code = "rate_limited" if error.status_code == 429 else "internal"
            yield "error", {"code": code, "message": UNAVAILABLE}
    except APIConnectionError as error:
        answer.stopped = f"Foundry connection error: {error}"
        yield "error", {"code": "internal", "message": UNAVAILABLE}


def ask(openai, agent_name: str, question: str, data: Dataset, inputs: dict) -> Answer:
    """One question in a new conversation, for the trial scripts and the measures."""
    conversation = openai.conversations.create()
    answer = Answer()
    for event, payload in turn(openai, agent_name, conversation.id, question, data, inputs, answer):
        if event == "error" and not answer.stopped:
            answer.stopped = payload["message"]
    return answer
