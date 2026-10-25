"""Run only these trusted local pilot snippets; exec is NOT an untrusted-code sandbox."""
import copy
import inspect
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"id", "category", "split", "problem_statement", "valid_input_domain", "function_signature", "reference_solution", "faulty_solution", "test_cases", "named_counterexample", "bug_explanation", "provenance", "human_review_status"}

def load_pilots():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "data/pilot").glob("*.json"))]

def candidate_function(problem, field):
    namespace = {}
    exec(compile(problem[field], "<trusted-local-pilot>", "exec"), namespace)
    name = problem["function_signature"].split("(")[0]
    function = namespace[name]
    if name + str(inspect.signature(function)) != problem["function_signature"]:
        raise ValueError("Candidate signature mismatch")
    return function

def case_result(function, case):
    args = copy.deepcopy(case["args"])
    before = copy.deepcopy(args)
    actual = function(*args)
    return {"name": case["name"], "kind": case["kind"], "expected": case["expected"], "actual": actual,
            "matches_expected": type(actual) is type(case["expected"]) and actual == case["expected"],
            "input_unchanged": args == before}

def evaluate(problem):
    return {field: [case_result(candidate_function(problem, field), case) for case in problem["test_cases"]]
            for field in ("reference_solution", "faulty_solution")}
