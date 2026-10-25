"""Validation functions for the main-study dataset."""
import ast
import copy
import inspect
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"id", "category", "split", "problem_statement", "valid_input_domain",
            "function_signature", "reference_solution", "faulty_solution",
            "test_cases", "named_counterexample", "bug_explanation",
            "provenance", "human_review_status"}

# Expanded allowed calls for the main study (superset of pilot's).
ALLOWED_CALLS = {"range", "enumerate", "sorted", "set", "len"}
ALLOWED_ATTRS = {"append", "lower", "upper"}


def load_main_tasks():
    """Load all main-study task JSON files sorted by name."""
    main_dir = ROOT / "data" / "main"
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(main_dir.glob("*.json"))]


def candidate_function(problem, field):
    """Exec the candidate code and return the function object."""
    namespace = {}
    exec(compile(problem[field], "<trusted-local-main>", "exec"), namespace)
    name = problem["function_signature"].split("(")[0]
    function = namespace[name]
    if name + str(inspect.signature(function)) != problem["function_signature"]:
        raise ValueError("Candidate signature mismatch")
    return function


def case_result(function, case):
    """Run one test case and return the result dict."""
    args = copy.deepcopy(case["args"])
    before = copy.deepcopy(args)
    actual = function(*args)
    expected = case["expected"]
    validation = case.get("validation", "exact")
    if validation == "index_in_bounds":
        # For binary search with duplicates: any index pointing to target is valid.
        lst = args[0]
        target = args[1]
        if isinstance(actual, int) and actual == -1 and target not in lst:
            matches = True
        elif isinstance(actual, int) and 0 <= actual < len(lst) and lst[actual] == target:
            matches = True
        else:
            matches = False
    else:
        matches = type(actual) is type(expected) and actual == expected
    return {
        "name": case["name"],
        "kind": case["kind"],
        "expected": expected,
        "actual": actual,
        "matches_expected": matches,
        "input_unchanged": args == before,
    }


def evaluate(problem):
    """Evaluate both candidates against all test cases."""
    return {
        field: [case_result(candidate_function(problem, field), case)
                for case in problem["test_cases"]]
        for field in ("reference_solution", "faulty_solution")
    }


def check_ast(problem, field):
    """Check AST constraints: single function, no imports, allowed calls only."""
    errors = []
    try:
        tree = ast.parse(problem[field])
    except SyntaxError as e:
        return [f"SyntaxError: {e}"]
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        errors.append("Expected exactly one function definition")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            errors.append("Imports are not allowed")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id not in ALLOWED_CALLS:
                errors.append(f"Disallowed call: {node.func.id}")
            elif isinstance(node.func, ast.Attribute) and node.func.attr not in ALLOWED_ATTRS:
                errors.append(f"Disallowed method call: .{node.func.attr}")
    return errors


def check_prompt_privacy(problem):
    """Verify no private metadata appears in judge prompts."""
    from src.prompts import build_prompt, CLAIM
    errors = []
    private_fields = {"bug_explanation", "named_counterexample",
                      "human_review_status", "provenance", "split",
                      "reference_solution", "faulty_solution"}
    for field in ("reference_solution", "faulty_solution"):
        code = problem[field]
        prompt_a = build_prompt(problem_statement=problem["problem_statement"],
                                candidate_code=code)
        prompt_b = build_prompt(problem_statement=problem["problem_statement"],
                                candidate_code=code, include_claim=True)
        for pf in private_fields:
            if pf in prompt_a:
                errors.append(f"Private field '{pf}' in condition A prompt")
            if pf in prompt_b:
                errors.append(f"Private field '{pf}' in condition B prompt")
        # Other candidate's code must not be in the prompt
        other = "faulty_solution" if field == "reference_solution" else "reference_solution"
        if problem[other] in prompt_a:
            errors.append(f"Other candidate's code found in prompt")
    return errors


def check_duplicates(tasks):
    """Check for duplicate or near-duplicate tasks."""
    errors = []
    # Check for identical problem statements
    seen_statements = {}
    for t in tasks:
        ps = t["problem_statement"]
        if ps in seen_statements:
            errors.append(f"Duplicate problem statement: {t['id']} and {seen_statements[ps]}")
        seen_statements[ps] = t["id"]
    # Check for identical function signatures
    seen_sigs = {}
    for t in tasks:
        sig = t["function_signature"]
        if sig in seen_sigs:
            errors.append(f"Duplicate function signature: {t['id']} and {seen_sigs[sig]}")
        seen_sigs[sig] = t["id"]
    # Check for identical reference solutions
    seen_refs = {}
    for t in tasks:
        ref = t["reference_solution"]
        if ref in seen_refs:
            errors.append(f"Duplicate reference solution: {t['id']} and {seen_refs[ref]}")
        seen_refs[ref] = t["id"]
    return errors
