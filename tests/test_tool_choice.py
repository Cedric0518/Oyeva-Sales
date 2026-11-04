from evals.tool_choice import CASES, succeeded


def test_a_certified_question_needs_its_function_and_no_code_interpreter():
    assert succeeded("sales_total", ["sales_total"])
    assert succeeded("sales_by_period", ["sales_by_period", "sales_by_period"])
    assert not succeeded("sales_total", ["sales_total", "code_interpreter"])
    assert not succeeded("sales_total", ["code_interpreter"])
    assert not succeeded("sales_total", [])


def test_a_control_question_needs_no_certified_function():
    assert succeeded(None, ["code_interpreter"])
    assert succeeded(None, [])
    assert not succeeded(None, ["sales_total"])


def test_the_cases_are_those_of_the_reading_rule():
    assert [case for case, *_ in CASES] == [*map(str, range(1, 11)), "C1", "C2"]
