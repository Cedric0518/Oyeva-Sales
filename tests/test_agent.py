"""The agent loop, with a fake Foundry client that plays scripted responses."""

import json
from pathlib import Path
from types import SimpleNamespace as Item

import pandas as pd

from api.agent import MAX_ROUNDS, ask
from api.tools import Dataset

DATA = Path(__file__).parent / "data"
QUESTION = "How much did we sell in 2025?"


class FakeOpenAI:
    """Returns the scripted responses in order and keeps every request the loop sends."""

    def __init__(self, *scripted):
        self.responses = self  # so that the loop can call openai.responses.create
        self.scripted = list(scripted)
        self.sent = []

    def create(self, **request):
        self.sent.append(request)
        return self.scripted.pop(0)


def response(response_id: str, *output, text: str = "") -> Item:
    return Item(id=response_id, output=list(output), output_text=text)


def function_call(name: str, call_id: str = "call_1", **arguments) -> Item:
    return Item(type="function_call", name=name, call_id=call_id, arguments=json.dumps(arguments))


def small_sales() -> Dataset:
    df = pd.read_csv(DATA / "small_sales.csv", parse_dates=["order_date"])
    return Dataset(df, {"date": "order_date", "amount": "amount"})


def test_a_result_goes_back_with_the_call_id_of_its_request():
    openai = FakeOpenAI(
        response("r1", function_call("sales_total", start="2025-01-01", end="2025-12-31")),
        response("r2", Item(type="message"), text="You sold $480.75 in 2025."),
    )
    answer = ask(openai, "oyeva-sales-agent", QUESTION, small_sales())
    first, second = openai.sent
    assert first["input"] == QUESTION
    assert first["extra_body"]["agent_reference"]["name"] == "oyeva-sales-agent"
    assert second["previous_response_id"] == "r1"
    sent_back = second["input"][0]
    assert sent_back["call_id"] == "call_1"
    assert json.loads(sent_back["output"])["value"] == 480.75
    assert answer.text == "You sold $480.75 in 2025."
    assert [name for name, *_ in answer.calls] == ["sales_total"]


def test_the_code_of_code_interpreter_is_kept():
    code = Item(type="code_interpreter_call", code="df['amount'].sum()")
    openai = FakeOpenAI(response("r1", code, text="Exploratory: 42."))
    answer = ask(openai, "oyeva-sales-agent", "Which weekday sells most?", small_sales())
    assert answer.code == ["df['amount'].sum()"]
    assert answer.calls == []


def test_the_same_failure_twice_stops_the_loop():
    bad = {"start": "2025-02-30", "end": "2025-12-31"}
    openai = FakeOpenAI(
        response("r1", function_call("sales_total", "call_1", **bad)),
        response("r2", function_call("sales_total", "call_2", **bad)),
    )
    answer = ask(openai, "oyeva-sales-agent", QUESTION, small_sales())
    assert answer.stopped.startswith("The same call failed twice")
    assert len(openai.sent) == 2


def test_the_loop_gives_up_after_five_rounds():
    calls = [
        response(
            f"r{i}", function_call("sales_total", f"call_{i}", start="2025-01-01", end="2025-12-31")
        )
        for i in range(MAX_ROUNDS + 1)
    ]
    openai = FakeOpenAI(*calls)
    answer = ask(openai, "oyeva-sales-agent", QUESTION, small_sales())
    assert answer.stopped == "No final answer after 5 rounds of function calls"
    assert len(openai.sent) == MAX_ROUNDS + 1
