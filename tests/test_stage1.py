import ast
import copy
import inspect
import json
import pytest
from src.prompts import CLAIM, build_prompt
from src.validation import REQUIRED, candidate_function, evaluate, load_pilots

PILOTS = load_pilots()

def test_inventory():
    assert len(PILOTS) == 5
    assert len({p["id"] for p in PILOTS}) == 5

@pytest.mark.parametrize("p", PILOTS, ids=lambda p: p["id"])
def test_schema(p):
    assert REQUIRED <= p.keys()
    assert all(p[key] for key in REQUIRED)
    assert p["human_review_status"] == "reviewed_with_ai_assistance"
    assert p["split"] == "pilot_debug_only"
    cases = p["test_cases"]
    assert len(cases) >= 5
    assert len({json.dumps(c["args"]) for c in cases}) == len(cases)
    assert len({c["name"] for c in cases}) == len(cases)
    assert p["named_counterexample"] in {c["name"] for c in cases}

@pytest.mark.parametrize("p", PILOTS, ids=lambda p: p["id"])
@pytest.mark.parametrize("field", ["reference_solution", "faulty_solution"])
def test_signature_and_simple_code(p, field):
    candidate_function(p, field)
    tree = ast.parse(p[field])
    assert len(tree.body) == 1 and isinstance(tree.body[0], ast.FunctionDef)
    allowed_calls = {"range", "enumerate", "sorted", "set"}
    for node in ast.walk(tree):
        assert not isinstance(node, (ast.Import, ast.ImportFrom))
        if isinstance(node, ast.Call):
            assert ((isinstance(node.func, ast.Name) and node.func.id in allowed_calls)
                    or (isinstance(node.func, ast.Attribute) and node.func.attr == "append"))

@pytest.mark.parametrize("p", PILOTS, ids=lambda p: p["id"])
def test_reference_cases(p):
    results = evaluate(p)["reference_solution"]
    assert all(c["matches_expected"] and c["input_unchanged"] for c in results), results

@pytest.mark.parametrize("p", PILOTS, ids=lambda p: p["id"])
def test_faulty_counterexample(p):
    results = evaluate(p)["faulty_solution"]
    counter = next(c for c in results if c["name"] == p["named_counterexample"])
    assert not counter["matches_expected"], counter
    assert all(c["input_unchanged"] for c in results)

@pytest.mark.parametrize("p", PILOTS, ids=lambda p: p["id"])
def test_faulty_valid_input_pass(p):
    results = evaluate(p)["faulty_solution"]
    # Apply the revised valid-input requirement to every candidate.
    assert any(c["matches_expected"] for c in results), results
    if p["id"] == "p05":
        zero = next(c for c in p["test_cases"] if c["name"] == "zero")
        assert zero["args"] == [0] and zero["kind"] == "boundary"
        assert zero["expected"] == 0
        actual = candidate_function(p, "faulty_solution")(*zero["args"])
        assert type(actual) is int and actual == 0
    else:
        # Retain the stronger ordinary-case checks already satisfied by p01-p04.
        assert any(c["kind"] == "ordinary" and c["matches_expected"] for c in results)

def test_sum_zero_passes_and_positive_cases_fail():
    p = next(p for p in PILOTS if p["id"] == "p05")
    results = evaluate(p)["faulty_solution"]
    assert p["named_counterexample"] == "one"
    one = next(c for c in p["test_cases"] if c["name"] == "one")
    assert one["args"] == [1] and one["expected"] == 1
    observed = next(c for c in results if c["name"] == "one")
    assert observed["actual"] == 0 and not observed["matches_expected"]
    assert [c["name"] for c in results if c["matches_expected"]] == ["zero"]
    assert all(not c["matches_expected"] for c in results if c["kind"] == "ordinary")

@pytest.mark.parametrize("p", PILOTS, ids=lambda p: p["id"])
@pytest.mark.parametrize("field", ["reference_solution", "faulty_solution"])
def test_prompt_pair_and_no_metadata(p, field):
    code = p[field]
    a = build_prompt(problem_statement=p["problem_statement"], candidate_code=code)
    b = build_prompt(problem_statement=p["problem_statement"], candidate_code=code, include_claim=True)
    expected = f"Problem statement:\n{p['problem_statement']}\n\nCandidate solution:\n```python\n{code}```"
    assert a == expected
    assert b == a + "\n\n" + CLAIM
    assert a.split("```python\n")[1].split("```")[0] == code
    assert b.split("```python\n")[1].split("```")[0] == code
    assert p["bug_explanation"] not in b
    assert p["named_counterexample"] not in b
    assert "reference_solution" not in b and "faulty_solution" not in b
    other = "faulty_solution" if field == "reference_solution" else "reference_solution"
    assert p[other] not in b
    # The only candidate label sent is the same neutral label in both conditions.
    assert "Candidate solution:" in a and "Candidate solution:" in b
    # Extra private fields cannot be serialized through this explicit API.
    with pytest.raises(TypeError):
        build_prompt(problem_statement=p["problem_statement"], candidate_code=code, bug_explanation="secret")

def test_allowlist_and_fixed_claim():
    assert set(inspect.signature(build_prompt).parameters) == {"problem_statement", "candidate_code", "include_claim"}
    with pytest.raises(TypeError):
        build_prompt(problem_statement="x", candidate_code="y", include_claim="custom claim")
