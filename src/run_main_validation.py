"""Run validation on the main-study dataset and write a report."""
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from src.main_validation import (
    ROOT, REQUIRED, ALLOWED_CALLS, ALLOWED_ATTRS,
    load_main_tasks, candidate_function, evaluate,
    check_ast, check_prompt_privacy, check_duplicates,
)

OUTPUT_DIR = ROOT / "outputs" / "main"
REPORT_PATH = OUTPUT_DIR / "validation_report.json"


def main():
    tasks = load_main_tasks()
    results = []

    for t in tasks:
        tid = t["id"]
        task_result = {"id": tid, "category": t["category"], "checks": {}}

        # Schema check
        schema_ok = REQUIRED <= t.keys() and all(t[k] for k in REQUIRED)
        task_result["checks"]["schema"] = "pass" if schema_ok else "fail"

        # Split check
        task_result["checks"]["split"] = "pass" if t.get("split") == "main_study" else "fail"

        # Review status check
        task_result["checks"]["review_status"] = "pass" if t.get("human_review_status") == "pending" else "fail"

        # Test case count
        task_result["checks"]["min_test_cases"] = "pass" if len(t.get("test_cases", [])) >= 8 else "fail"

        # Unique test case args and names
        cases = t.get("test_cases", [])
        args_unique = len({json.dumps(c["args"]) for c in cases}) == len(cases)
        names_unique = len({c["name"] for c in cases}) == len(cases)
        task_result["checks"]["unique_test_args"] = "pass" if args_unique else "fail"
        task_result["checks"]["unique_test_names"] = "pass" if names_unique else "fail"

        # Named counterexample exists
        ce_exists = t.get("named_counterexample") in {c["name"] for c in cases}
        task_result["checks"]["counterexample_exists"] = "pass" if ce_exists else "fail"

        # AST checks
        ref_ast = check_ast(t, "reference_solution")
        flt_ast = check_ast(t, "faulty_solution")
        task_result["checks"]["reference_ast"] = "pass" if not ref_ast else {"fail": ref_ast}
        task_result["checks"]["faulty_ast"] = "pass" if not flt_ast else {"fail": flt_ast}

        # Signature match
        try:
            candidate_function(t, "reference_solution")
            candidate_function(t, "faulty_solution")
            task_result["checks"]["signature_match"] = "pass"
        except Exception as e:
            task_result["checks"]["signature_match"] = {"fail": str(e)}

        # Reference passes all
        try:
            eval_results = evaluate(t)
            ref_all_pass = all(c["matches_expected"] and c["input_unchanged"]
                               for c in eval_results["reference_solution"])
            task_result["checks"]["reference_passes_all"] = "pass" if ref_all_pass else "fail"
        except Exception as e:
            task_result["checks"]["reference_passes_all"] = {"fail": str(e)}
            eval_results = None

        # Faulty fails counterexample
        if eval_results:
            flt_results = eval_results["faulty_solution"]
            ce = next((c for c in flt_results if c["name"] == t["named_counterexample"]), None)
            task_result["checks"]["faulty_fails_counterexample"] = "pass" if (ce and not ce["matches_expected"]) else "fail"

            # Faulty passes at least one ordinary
            passes_ordinary = any(c["kind"] == "ordinary" and c["matches_expected"] for c in flt_results)
            task_result["checks"]["faulty_passes_ordinary"] = "pass" if passes_ordinary else "fail"

            # Input non-mutation
            all_unchanged = all(c["input_unchanged"] for c in flt_results)
            task_result["checks"]["input_unchanged"] = "pass" if all_unchanged else "fail"
        else:
            task_result["checks"]["faulty_fails_counterexample"] = "skip"
            task_result["checks"]["faulty_passes_ordinary"] = "skip"
            task_result["checks"]["input_unchanged"] = "skip"

        # Prompt privacy
        privacy_errors = check_prompt_privacy(t)
        task_result["checks"]["prompt_privacy"] = "pass" if not privacy_errors else {"fail": privacy_errors}

        # Overall
        all_checks = [v for v in task_result["checks"].values() if v != "skip"]
        task_result["overall"] = "pass" if all(v == "pass" for v in all_checks) else "fail"

        results.append(task_result)

    # Duplicate check
    dup_errors = check_duplicates(tasks)

    # Summary
    all_pass = all(r["overall"] == "pass" for r in results) and not dup_errors
    report = {
        "stage": "main_study_validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "total_tasks": len(tasks),
        "all_checks_passed": all_pass,
        "allowed_calls": sorted(ALLOWED_CALLS),
        "allowed_attrs": sorted(ALLOWED_ATTRS),
        "duplicate_check": "pass" if not dup_errors else {"fail": dup_errors},
        "task_results": results,
        "sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "data" / "main").glob("*.json"))
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {REPORT_PATH}")
    print(f"Tasks: {len(tasks)}, All passed: {all_pass}")

    # Generate review sheet
    review_path = OUTPUT_DIR / "review_sheet.md"
    lines = ["# Main Study Review Sheet", "",
             f"Generated: {report['generated_at_utc']}", "",
             "All human-review statuses are pending. No API calls were made.", "",
             "| ID | Category | Function | Bug Summary | Counterexample | Ordinary Pass |",
             "|-----|----------|----------|-------------|----------------|---------------|"]
    for t in tasks:
        lines.append(
            f"| {t['id']} | {t['category']} | `{t['function_signature']}` | "
            f"{t['bug_explanation'][:80]}... | "
            f"{t['named_counterexample']} | "
            f"{'yes' if any(r['checks'].get('faulty_passes_ordinary') == 'pass' for r in results if r['id'] == t['id']) else 'no'} |"
        )
    lines.append("")
    lines.append("## By Category")
    from collections import defaultdict
    by_cat = defaultdict(list)
    for t in tasks:
        by_cat[t["category"]].append(t)
    for cat in sorted(by_cat):
        lines.append(f"\n### {cat}\n")
        for t in by_cat[cat]:
            lines.append(f"**{t['id']}**: `{t['function_signature']}`")
            lines.append(f"- Spec: {t['problem_statement']}")
            lines.append(f"- Bug: {t['bug_explanation']}")
            lines.append(f"- Counterexample: {t['named_counterexample']}")
            lines.append(f"- Tests: {len(t['test_cases'])} cases")
            lines.append("")
    review_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Review sheet: {review_path}")

    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
