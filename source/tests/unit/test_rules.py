import math
import pytest
from app.core.errors import DomainError
from app.rules.engine import validate_question_config, trace_path_and_validate_submission, validate_answer, evaluate_condition, MISSING
from tests.fixtures import fixture_questions, answers


@pytest.mark.parametrize("values,path", [
    ({"q1": "no", "q3": 8}, ["q1", "q3"]),
    ({"q1": "no", "q3": 12}, ["q1", "q3", "q4"]),
    ({"q1": "yes", "q2": ["python", "java"]}, ["q1", "q2", "q4"]),
    ({"q1": "yes", "q2": ["cpp"]}, ["q1", "q2"]),
    ({"q1": "yes", "q2": ["python", "java", "cpp"]}, ["q1", "q2", "q4"]),
], ids=["R01", "R02", "R03", "R04", "R05"])
def test_fixed_paths(values, path):
    qs = validate_question_config(fixture_questions())
    actual, visited = trace_path_and_validate_submission(qs, answers(**values))
    assert visited == path
    assert len(actual) == len(values)


@pytest.mark.parametrize("values", [
    {"q1": "no"}, {"q1": "yes", "q2": ["python", "python"]},
    {"q1": "yes", "q2": ["cpp"], "q3": 3}, {"q1": "no", "q3": -1}, {"q1": "no", "q3": "12"},
], ids=["R06", "R07", "R08", "R09", "R10"])
def test_fixed_invalid(values):
    with pytest.raises(DomainError): trace_path_and_validate_submission(fixture_questions(), answers(**values))


@pytest.mark.parametrize("case", range(5), ids=["R11", "R12", "R13", "R14", "R15"])
def test_bad_config(case):
    qs = fixture_questions()
    if case == 0: qs[1]["routingRules"][0]["target"]["questionId"] = "q99"
    if case == 1: qs[2]["routingRules"][0]["target"]["questionId"] = "q1"
    if case == 2: qs[1]["routingRules"][1]["priority"] = 10
    if case == 3: qs[0]["routingRules"][0]["condition"]["operator"] = "contains_all"
    if case == 4: qs[1]["validation"] = {"minSelections": 3, "maxSelections": 2}
    with pytest.raises(DomainError): validate_question_config(qs)


@pytest.mark.parametrize("value", ["12", True, False, math.nan, math.inf, -math.inf, "", [], {}, 2**63, 10**1000])
def test_number_rejects(value):
    with pytest.raises(DomainError): validate_answer(fixture_questions()[2], value)


@pytest.mark.parametrize("value", [0, 80, 0.5, 12])
def test_number_bounds(value): assert validate_answer(fixture_questions()[2], value) == value


def test_integer_and_negative():
    q = fixture_questions()[2]; q["validation"] = {"integerOnly": True, "min": -5, "max": 120}
    assert validate_answer(q, -5) == -5
    assert validate_answer(q, 120) == 120
    with pytest.raises(DomainError): validate_answer(q, 1.5)


@pytest.mark.parametrize("t,value", [("text", "  "), ("text", None), ("multiple_choice", []), ("multiple_choice", None), ("number", None)])
def test_optional_empty(t, value):
    q = next(q for q in fixture_questions() if q["type"] == t); q["required"] = False
    assert validate_answer(q, value) is MISSING
    q["required"] = True
    with pytest.raises(DomainError): validate_answer(q, value)


@pytest.mark.parametrize("value", [3, {}, [], "bad", ""])
def test_single_invalid(value):
    with pytest.raises(DomainError): validate_answer(fixture_questions()[0], value)


def test_text_unicode_and_boundary():
    q = fixture_questions()[3]; q["validation"] = {"minLength": 2, "maxLength": 3}
    assert validate_answer(q, "  中文😀 ") == "中文😀"
    for value in ["a", "abcd", 12, []]:
        with pytest.raises(DomainError): validate_answer(q, value)


def test_multiselect_boundaries():
    q = fixture_questions()[1]; q["required"] = False; q["validation"] = {"minSelections": 2, "maxSelections": 2}
    assert validate_answer(q, []) is MISSING
    assert validate_answer(q, ["java", "python"]) == ["python", "java"]
    for value in [["python"], ["python", "java", "cpp"], ["bad"], "python", [1], [["x"]]]:
        with pytest.raises(DomainError): validate_answer(q, value)


@pytest.mark.parametrize("op,rhs,value,expected", [
    ("eq", 3, 3, True), ("eq", 3, 4, False), ("gt", 3, 4, True), ("gt", 3, 3, False),
    ("gte", 3, 3, True), ("gte", 3, 2, False), ("lt", 3, 2, True), ("lt", 3, 3, False),
    ("lte", 3, 3, True), ("lte", 3, 4, False), ("contains_any", ["a"], ["a", "b"], True),
    ("contains_any", ["a"], ["b"], False), ("contains_all", ["a", "b"], ["a", "b", "c"], True), ("contains_all", ["a", "b"], ["a"], False),
])
def test_operators(op, rhs, value, expected): assert evaluate_condition({"operator": op, "operand": rhs}, value) is expected


@pytest.mark.parametrize("mutation", ["self", "target_end", "operand", "rule_id", "question_id", "options", "integer", "range", "text_limit", "validation_key", "empty"])
def test_configuration_edges(mutation):
    qs = fixture_questions()
    if mutation == "self": qs[0]["routingRules"][0]["target"]["questionId"] = "q1"
    if mutation == "target_end": qs[0]["routingRules"][0]["target"] = {"kind": "end", "questionId": "q4"}
    if mutation == "operand": qs[1]["routingRules"][0]["condition"]["operand"] = []
    if mutation == "rule_id": qs[1]["routingRules"][1]["id"] = "r2"
    if mutation == "question_id": qs[2]["id"] = "q1"
    if mutation == "options": qs[0]["options"][1]["id"] = "yes"
    if mutation == "integer": qs[2]["validation"]["integerOnly"] = 1
    if mutation == "range": qs[2]["validation"]["min"] = 81
    if mutation == "text_limit": qs[3]["validation"]["maxLength"] = 10001
    if mutation == "validation_key": qs[3]["validation"]["max"] = 1
    if mutation == "empty": qs = []
    with pytest.raises(DomainError): validate_question_config(qs)


def test_optional_no_rule_and_default():
    qs = fixture_questions(); qs[0]["required"] = False
    normalized, path = trace_path_and_validate_submission(qs, answers(q2=["python"], q3=0))
    assert path == ["q1", "q2", "q3"]  # unanswered q1 -> next; unmatched q2 -> next
    assert normalized[0]["questionId"] == "q2"
    with pytest.raises(DomainError): trace_path_and_validate_submission(qs, answers(q2=["cpp"]) * 2)
