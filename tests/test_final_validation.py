from src.final_validation import ORACLES, faulty_passes_valid_case, get_fn, load_all, run_case


def test_m09_oracle_matches_all_stored_expected_values():
    task = next(task for _, task in load_all() if task["id"] == "m09")
    oracle = ORACLES["m09"]

    assert [oracle(*case["args"]) for case in task["test_cases"]] == [
        case["expected"] for case in task["test_cases"]
    ]


def test_p05_boundary_pass_satisfies_faulty_valid_case_rule():
    task = next(task for _, task in load_all() if task["id"] == "p05")
    faulty = get_fn(task, "faulty_solution")
    results = [run_case(faulty, case) for case in task["test_cases"]]

    assert faulty_passes_valid_case(results)
    counterexample = next(
        result for result in results if result["name"] == task["named_counterexample"]
    )
    assert not counterexample["match"]
    assert any(
        result["name"] == "zero"
        and result["kind"] == "boundary"
        and result["match"]
        for result in results
    )


def test_passing_edge_case_alone_does_not_satisfy_revised_rule():
    assert not faulty_passes_valid_case([{"match": True, "kind": "edge"}])
