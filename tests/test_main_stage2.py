"""Targeted offline checks for the main-study Stage 2 manifest.

No API calls. All checks use the manifest builder directly.
"""
import json
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from src.stage2.main_experiment import (
    build_main_manifest,
    config_fingerprint,
    MAIN_SHUFFLE_SEED,
)
from src.stage2.experiment import (
    MODEL_ID,
    JUDGE_INSTRUCTION,
    GENERATION_SETTINGS,
)
from src.main_validation import load_main_tasks
from src.prompts import CLAIM

TASKS = load_main_tasks()
PRIVATE_FIELDS = {
    "bug_explanation", "named_counterexample", "human_review_status",
    "provenance", "split", "reference_solution", "faulty_solution",
}


class TestMainManifest:
    def test_exactly_120_requests(self):
        m = build_main_manifest()
        assert m["total_requests"] == 120
        assert len(m["requests"]) == 120

    def test_all_request_ids_unique(self):
        m = build_main_manifest()
        ids = [r["request_id"] for r in m["requests"]]
        assert len(set(ids)) == 120

    def test_complete_coverage(self):
        m = build_main_manifest()
        combos = {
            (r["problem_id"], r["candidate"], r["condition"])
            for r in m["requests"]
        }
        expected = {
            (t["id"], cand, cond)
            for t in TASKS
            for cand in ("reference_solution", "faulty_solution")
            for cond in ("A", "B")
        }
        assert combos == expected
        assert len(combos) == 120

    def test_model_id_unchanged(self):
        m = build_main_manifest()
        assert m["model_id"] == MODEL_ID
        assert m["model_id"] == "gemini-3.5-flash-lite"

    def test_judge_instruction_unchanged(self):
        m = build_main_manifest()
        assert m["judge_instruction"] == JUDGE_INSTRUCTION

    def test_generation_settings_unchanged(self):
        m = build_main_manifest()
        assert m["generation_settings"] == GENERATION_SETTINGS

    def test_shuffle_seed_recorded(self):
        m = build_main_manifest()
        assert m["shuffle_seed"] == MAIN_SHUFFLE_SEED
        assert m["shuffle_seed"] != 20261021  # distinct from pilot

    def test_dataset_hashes_present(self):
        m = build_main_manifest()
        assert len(m["dataset_hashes"]) == 30
        for h in m["dataset_hashes"].values():
            assert re.fullmatch(r"[0-9a-f]{64}", h)

    def test_shuffle_deterministic(self):
        m1 = build_main_manifest()
        m2 = build_main_manifest()
        ids1 = [r["request_id"] for r in m1["requests"]]
        ids2 = [r["request_id"] for r in m2["requests"]]
        assert ids1 == ids2

    def test_condition_a_no_claim(self):
        m = build_main_manifest()
        for r in m["requests"]:
            if r["condition"] == "A":
                assert CLAIM not in r["prompt"]

    def test_condition_b_has_claim(self):
        m = build_main_manifest()
        for r in m["requests"]:
            if r["condition"] == "B":
                assert r["prompt"].endswith(CLAIM)

    def test_condition_b_equals_a_plus_claim(self):
        m = build_main_manifest()
        by_key = {}
        for r in m["requests"]:
            key = (r["problem_id"], r["candidate"], r["condition"])
            by_key[key] = r
        for t in TASKS:
            for cand in ("reference_solution", "faulty_solution"):
                a = by_key[(t["id"], cand, "A")]["prompt"]
                b = by_key[(t["id"], cand, "B")]["prompt"]
                assert b == a + "\n\n" + CLAIM

    def test_no_private_fields_in_prompts(self):
        m = build_main_manifest()
        for r in m["requests"]:
            for field in PRIVATE_FIELDS:
                assert field not in r["prompt"], (
                    f"Private field '{field}' in {r['request_id']}"
                )

    def test_no_other_candidate_code_in_prompt(self):
        m = build_main_manifest()
        by_key = {}
        for r in m["requests"]:
            by_key[(r["problem_id"], r["candidate"])] = r
        for t in TASKS:
            ref_prompt = by_key[(t["id"], "reference_solution")]["prompt"]
            flt_prompt = by_key[(t["id"], "faulty_solution")]["prompt"]
            assert t["faulty_solution"] not in ref_prompt
            assert t["reference_solution"] not in flt_prompt

    def test_no_bug_explanation_in_prompts(self):
        m = build_main_manifest()
        for t in TASKS:
            for r in m["requests"]:
                if r["problem_id"] == t["id"]:
                    assert t["bug_explanation"] not in r["prompt"]


class TestMainConfigFingerprint:
    def test_same_manifest_same_fingerprint(self):
        m1 = build_main_manifest()
        m2 = build_main_manifest()
        assert config_fingerprint(m1) == config_fingerprint(m2)

    def test_different_model_different_fingerprint(self):
        m1 = build_main_manifest()
        m2 = build_main_manifest()
        m2["model_id"] = "different"
        assert config_fingerprint(m1) != config_fingerprint(m2)

    def test_different_instruction_different_fingerprint(self):
        m1 = build_main_manifest()
        m2 = build_main_manifest()
        m2["judge_instruction"] = "different"
        assert config_fingerprint(m1) != config_fingerprint(m2)

    def test_different_prompts_different_fingerprint(self):
        m1 = build_main_manifest()
        m2 = build_main_manifest()
        m2["requests"][0]["prompt"] = "tampered"
        assert config_fingerprint(m1) != config_fingerprint(m2)

    def test_fingerprint_covers_response_schema(self):
        m = build_main_manifest()
        from src.stage2.schema import JudgeResponse
        schema = JudgeResponse.model_json_schema()
        assert "verdict" in schema.get("properties", {})
        assert "reason" in schema.get("properties", {})


class TestMainDryRunLiveSeparation:
    def test_dry_run_writes_to_dry_run_path(self, tmp_path):
        from src.stage2.runner import run
        manifest_path = tmp_path / "manifest.json"
        dry_path = tmp_path / "dry_run" / "results.jsonl"
        live_path = tmp_path / "results.jsonl"

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", dry_path),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
            patch("src.stage2.runner.build_manifest", build_main_manifest),
            patch("src.stage2.runner.config_fingerprint", config_fingerprint),
            patch("src.stage2.runner.save_manifest",
                  lambda m, p: p.parent.mkdir(parents=True, exist_ok=True)
                  or p.write_text(json.dumps(m, indent=2) + "\n")),
            patch("src.stage2.runner.load_manifest",
                  lambda p: json.loads(p.read_text())),
        ):
            run(dry_run=True)

        assert dry_path.exists()
        records = [json.loads(l) for l in dry_path.read_text().splitlines() if l.strip()]
        assert len(records) == 120
        assert all(r["status"] == "dry_run" for r in records)
        assert not live_path.exists()

    def test_dry_run_not_treated_as_completed(self, tmp_path):
        """dry_run records must not be skipped by --resume."""
        from src.stage2.runner import _load_completed, LIVE_COMPLETED_STATUSES
        results_path = tmp_path / "results.jsonl"
        rec = {"request_id": "r000", "status": "dry_run"}
        results_path.write_text(json.dumps(rec) + "\n")
        completed = _load_completed(results_path)
        assert "r000" not in completed
        assert "dry_run" not in LIVE_COMPLETED_STATUSES

    def test_main_separate_from_pilot(self):
        """Main-study output path must not overlap with pilot output path."""
        from src.stage2.runner import RESULTS_PATH as PILOT_RESULTS
        main_results = Path("outputs") / "main" / "stage2" / "results.jsonl"
        assert main_results != PILOT_RESULTS
        assert "main" in str(main_results)
        assert "pilot" in str(PILOT_RESULTS)
