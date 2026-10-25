"""Tests for the main-study dataset."""
import ast
import json
import pytest
from src.main_validation import (
    REQUIRED, ALLOWED_CALLS, ALLOWED_ATTRS,
    load_main_tasks, candidate_function, evaluate,
    check_ast, check_prompt_privacy, check_duplicates,
)

TASKS = load_main_tasks()


def test_inventory():
    assert len(TASKS) == 30
    ids = [t["id"] for t in TASKS]
    assert len(set(ids)) == 30
    assert all(t["id"].startswith("m") for t in TASKS)


def test_categories():
    from collections import Counter
    cats = Counter(t["category"] for t in TASKS)
    assert len(cats) == 6
    assert all(count == 5 for count in cats.values())


@pytest.mark.parametrize("t", TASKS, ids=lambda t: t["id"])
def test_schema(t):
    assert REQUIRED <= t.keys()
    assert all(t[key] for key in REQUIRED)
    assert t["split"] == "main_study"
    assert t["human_review_status"] == "reviewed_with_ai_assistance"
    cases = t["test_cases"]
    assert len(cases) >= 8
    assert len({json.dumps(c["args"]) for c in cases}) == len(cases)
    assert len({c["name"] for c in cases}) == len(cases)
    assert t["named_counterexample"] in {c["name"] for c in cases}


@pytest.mark.parametrize("t", TASKS, ids=lambda t: t["id"])
@pytest.mark.parametrize("field", ["reference_solution", "faulty_solution"])
def test_ast_constraints(t, field):
    errors = check_ast(t, field)
    assert not errors, f"{t['id']} {field}: {errors}"


@pytest.mark.parametrize("t", TASKS, ids=lambda t: t["id"])
@pytest.mark.parametrize("field", ["reference_solution", "faulty_solution"])
def test_signature_match(t, field):
    candidate_function(t, field)


@pytest.mark.parametrize("t", TASKS, ids=lambda t: t["id"])
def test_reference_passes_all(t):
    results = evaluate(t)["reference_solution"]
    assert all(c["matches_expected"] and c["input_unchanged"] for c in results), results


@pytest.mark.parametrize("t", TASKS, ids=lambda t: t["id"])
def test_faulty_fails_counterexample(t):
    results = evaluate(t)["faulty_solution"]
    counter = next(c for c in results if c["name"] == t["named_counterexample"])
    assert not counter["matches_expected"], counter


@pytest.mark.parametrize("t", TASKS, ids=lambda t: t["id"])
def test_faulty_passes_ordinary(t):
    results = evaluate(t)["faulty_solution"]
    assert any(c["kind"] == "ordinary" and c["matches_expected"] for c in results), results


@pytest.mark.parametrize("t", TASKS, ids=lambda t: t["id"])
def test_faulty_input_unchanged(t):
    results = evaluate(t)["faulty_solution"]
    assert all(c["input_unchanged"] for c in results), results


@pytest.mark.parametrize("t", TASKS, ids=lambda t: t["id"])
def test_prompt_privacy(t):
    errors = check_prompt_privacy(t)
    assert not errors, f"{t['id']}: {errors}"


def test_no_duplicates():
    errors = check_duplicates(TASKS)
    assert not errors, errors


def test_no_pilot_reuse():
    """No main-study task should be a duplicate of a pilot task."""
    from src.validation import load_pilots
    pilots = load_pilots()
    pilot_sigs = {p["function_signature"] for p in pilots}
    pilot_stmts = {p["problem_statement"] for p in pilots}
    for t in TASKS:
        assert t["function_signature"] not in pilot_sigs, (
            f"{t['id']} reuses pilot signature")
        assert t["problem_statement"] not in pilot_stmts, (
            f"{t['id']} reuses pilot problem statement")


@pytest.mark.parametrize("t", TASKS, ids=lambda t: t["id"])
def test_claim_unchanged(t):
    """The fixed claim must be the pilot's claim."""
    from src.prompts import CLAIM, build_prompt
    prompt_b = build_prompt(
        problem_statement=t["problem_statement"],
        candidate_code=t["reference_solution"],
        include_claim=True,
    )
    assert prompt_b.endswith(CLAIM)


@pytest.mark.parametrize("t", TASKS, ids=lambda t: t["id"])
def test_allowed_calls_expanded(t):
    """Main study allowed calls must be a superset of pilot's."""
    assert {"range", "enumerate", "sorted", "set"} <= ALLOWED_CALLS
    assert "append" in ALLOWED_ATTRS
