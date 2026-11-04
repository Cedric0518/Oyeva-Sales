"""The agent loop: ask Foundry, run the functions the agent asks for, send back their results.

Code Interpreter runs at Foundry, inside the response. The certified functions run here, on the
session data: the agent only receives their results.
"""

import json
from dataclasses import dataclass, field

from api.tools import Dataset, run_tool

MAX_ROUNDS = 5  # rounds of function calls before giving up


@dataclass
class Answer:
    text: str = ""
    calls: list = field(default_factory=list)  # (tool, arguments, result) for each function call
    code: list = field(default_factory=list)  # the code that Code Interpreter ran
    stopped: str | None = None  # why the loop stopped without a final answer


def of_type(response, kind: str) -> list:
    return [item for item in response.output if item.type == kind]


def ask(openai, agent_name: str, question: str, data: Dataset) -> Answer:
    agent = {"agent_reference": {"name": agent_name, "type": "agent_reference"}}
    response = openai.responses.create(input=question, extra_body=agent)
    answer, failed = Answer(), set()
    for _ in range(MAX_ROUNDS):
        answer.code += [item.code or "" for item in of_type(response, "code_interpreter_call")]
        requests = of_type(response, "function_call")
        if not requests:
            answer.text = response.output_text
            return answer
        outputs = []
        for item in requests:
            result = run_tool(item.name, item.arguments, data)
            answer.calls.append((item.name, item.arguments, result))
            if result["status"] == "error":
                if (item.name, item.arguments) in failed:
                    answer.stopped = f"The same call failed twice: {item.name} {item.arguments}"
                    return answer
                failed.add((item.name, item.arguments))
            outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(result),
                }
            )
        response = openai.responses.create(
            input=outputs, previous_response_id=response.id, extra_body=agent
        )
    answer.stopped = f"No final answer after {MAX_ROUNDS} rounds of function calls"
    return answer
