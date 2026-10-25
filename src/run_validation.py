"""Run pytest and write actual local observations, including any failures."""
import hashlib
import json
import platform
from datetime import datetime, timezone
import pytest
from src.validation import ROOT, evaluate, load_pilots

class Results:
    def __init__(self):
        self.tests = []
    def pytest_runtest_logreport(self, report):
        if report.when == "call" or report.failed:
            self.tests.append({"nodeid": report.nodeid, "phase": report.when,
                               "outcome": "xfail" if hasattr(report, "wasxfail") else report.outcome,
                               "detail": str(report.longrepr) if report.longrepr else None})

def main():
    recorder = Results()
    code = int(pytest.main([str(ROOT / "tests"), "-q", "-ra"], plugins=[recorder]))
    pilots = []
    for p in load_pilots():
        try:
            pilots.append({"id": p["id"], "named_counterexample": p["named_counterexample"],
                           "human_review_status": p["human_review_status"], "results": evaluate(p)})
        except Exception as error:
            pilots.append({"id": p["id"], "error": repr(error)})
            code = code or 1
    report = {"stage": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "pytest": pytest.__version__, "pytest_exit_code": code,
              "all_requested_requirements_satisfied": code == 0 and bool(recorder.tests) and all(t["outcome"] == "passed" for t in recorder.tests),
              "requirements_revision": "Stage 1 valid-input revision, user requested",
              "faulty_pass_requirement": "Each faulty solution must pass at least one valid test input. This may be an ordinary or boundary case.",
              "requirement_change_reason": "The p05 range(1, n) bug fails every positive n and passes n=0. The previous ordinary-case requirement conflicted with that bug.",
              "historical_report": "outputs/pilot/history/stage1_validation_before_requirement_revision.json",
              "design_exception": None,
              "llm_calls": 0, "behavioural_conclusions": None, "tests": recorder.tests, "pilots": pilots,
              "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for folder in ("data/pilot", "src", "tests") for p in sorted((ROOT/folder).glob("*")) if p.is_file()}}
    destination = ROOT / "outputs/pilot/stage1_validation.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Report: outputs/pilot/stage1_validation.json")
    raise SystemExit(code)

if __name__ == "__main__":
    main()
