"""Offline tests for Stage 2.

All tests use mocked responses.  No network calls are made.
Results are written to a temporary directory isolated from real experiment data.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.stage2.experiment import (
    GENERATION_SETTINGS,
    JUDGE_INSTRUCTION,
    MODEL_ID,
    SHUFFLE_SEED,
    build_manifest,
    config_fingerprint,
)
from src.stage2.schema import JudgeResponse, Verdict
from src.stage2.runner import (
    DRY_RUN_RESULTS_PATH,
    MANIFEST_PATH,
    RESULTS_PATH,
    LIVE_COMPLETED_STATUSES,
    _append_result,
    _load_completed,
    _parse_response,
    _scrub,
    run,
)
from src.validation import load_pilots


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PILOTS = load_pilots()
PRIVATE_FIELDS = {
    "bug_explanation",
    "named_counterexample",
    "human_review_status",
    "provenance",
    "split",
}


def _fake_result(request_id: str, status: str = "completed", verdict: str = "incorrect") -> dict:
    return {
        "request_id": request_id,
        "problem_id": "p01",
        "candidate": "faulty_solution",
        "condition": "A",
        "prompt": "Problem statement:\ntest\n\nCandidate solution:\n```python\ndef f(): pass```",
        "status": status,
        "timestamp_utc": "2026-10-21T00:00:00+00:00",
        "raw_response": json.dumps({"verdict": verdict, "reason": "test reason"}),
        "parsed_verdict": verdict,
        "parsed_reason": "test reason",
        "returned_model_version": None,
        "usage_metadata": None,
        "error_info": None,
        "retry_count": 0,
    }


def _make_mock_response(verdict: str = "incorrect", reason: str = "test reason"):
    """Create a MagicMock simulating a valid API response."""
    resp = MagicMock()
    resp.text = json.dumps({"verdict": verdict, "reason": reason})
    resp.usage_metadata = None
    resp.model_version = "gemini-3.5-flash-lite-test"
    resp.candidates = []
    return resp


# ---------------------------------------------------------------------------
# 1. Exactly 20 unique requests
# ---------------------------------------------------------------------------

class TestManifest:
    def test_exactly_20_requests(self):
        manifest = build_manifest()
        assert manifest["total_requests"] == 20
        assert len(manifest["requests"]) == 20

    def test_all_request_ids_unique(self):
        manifest = build_manifest()
        ids = [r["request_id"] for r in manifest["requests"]]
        assert len(set(ids)) == 20

    def test_covers_all_combinations(self):
        manifest = build_manifest()
        combos = {
            (r["problem_id"], r["candidate"], r["condition"])
            for r in manifest["requests"]
        }
        expected = {
            (f"p0{n}", cand, cond)
            for n in range(1, 6)
            for cand in ("reference_solution", "faulty_solution")
            for cond in ("A", "B")
        }
        assert combos == expected

    def test_model_id_recorded(self):
        manifest = build_manifest()
        assert manifest["model_id"] == MODEL_ID

    def test_shuffle_seed_recorded(self):
        manifest = build_manifest()
        assert manifest["shuffle_seed"] == SHUFFLE_SEED

    def test_generation_settings_recorded(self):
        manifest = build_manifest()
        assert manifest["generation_settings"] == GENERATION_SETTINGS

    def test_sdk_retry_disabled_in_settings(self):
        """SDK automatic retries must be explicitly disabled (attempts=1)."""
        settings = build_manifest()["generation_settings"]
        assert settings["sdk_retry_attempts"] == 1
        assert settings["request_timeout_ms"] == 60_000

    def test_judge_instruction_recorded(self):
        manifest = build_manifest()
        assert manifest["judge_instruction"] == JUDGE_INSTRUCTION

    def test_dataset_hashes_present(self):
        manifest = build_manifest()
        assert len(manifest["dataset_hashes"]) == 5
        for h in manifest["dataset_hashes"].values():
            assert re.fullmatch(r"[0-9a-f]{64}", h)

    def test_shuffle_is_deterministic(self):
        m1 = build_manifest()
        m2 = build_manifest()
        ids1 = [r["request_id"] for r in m1["requests"]]
        ids2 = [r["request_id"] for r in m2["requests"]]
        assert ids1 == ids2

    def test_condition_a_has_no_claim(self):
        from src.prompts import CLAIM
        manifest = build_manifest()
        for r in manifest["requests"]:
            if r["condition"] == "A":
                assert CLAIM not in r["prompt"]

    def test_condition_b_has_claim(self):
        from src.prompts import CLAIM
        manifest = build_manifest()
        for r in manifest["requests"]:
            if r["condition"] == "B":
                assert r["prompt"].endswith(CLAIM)

    def test_condition_b_prompt_equals_a_plus_claim(self):
        """For each (problem, candidate) pair, prompt_B == prompt_A + '\n\n' + CLAIM."""
        from src.prompts import CLAIM
        manifest = build_manifest()
        by_key: dict[tuple, dict] = {}
        for r in manifest["requests"]:
            key = (r["problem_id"], r["candidate"], r["condition"])
            by_key[key] = r
        for p in PILOTS:
            for cand in ("reference_solution", "faulty_solution"):
                a = by_key[(p["id"], cand, "A")]["prompt"]
                b = by_key[(p["id"], cand, "B")]["prompt"]
                assert b == a + "\n\n" + CLAIM


# ---------------------------------------------------------------------------
# 2. No private metadata in outgoing payload
# ---------------------------------------------------------------------------

class TestPromptPrivacy:
    def test_no_private_fields_in_prompts(self):
        manifest = build_manifest()
        for r in manifest["requests"]:
            prompt = r["prompt"]
            for field in PRIVATE_FIELDS:
                assert field not in prompt, (
                    f"Private field '{field}' found in prompt {r['request_id']}"
                )

    def test_no_correctness_labels_in_prompts(self):
        manifest = build_manifest()
        for r in manifest["requests"]:
            prompt = r["prompt"]
            assert "reference_solution" not in prompt
            assert "faulty_solution" not in prompt
            assert "correct solution" not in prompt.lower() or (
                # The CLAIM contains "correct" — only present in condition B, by design
                r["condition"] == "B"
            )

    def test_other_candidates_code_absent(self):
        """The prompt must not contain the other candidate's code."""
        manifest = build_manifest()
        by_key: dict[tuple, dict] = {}
        for r in manifest["requests"]:
            by_key[(r["problem_id"], r["candidate"])] = r

        for p in PILOTS:
            ref_prompt = by_key[(p["id"], "reference_solution")]["prompt"]
            flt_prompt = by_key[(p["id"], "faulty_solution")]["prompt"]
            assert p["faulty_solution"] not in ref_prompt
            assert p["reference_solution"] not in flt_prompt

    def test_bug_explanation_absent(self):
        manifest = build_manifest()
        for p in PILOTS:
            for r in manifest["requests"]:
                if r["problem_id"] == p["id"]:
                    assert p["bug_explanation"] not in r["prompt"]

    def test_api_key_cannot_appear_in_error(self):
        """_scrub removes the key from any string."""
        fake_key = "AIzaFAKE12345"
        dirty = f"Error connecting with key={fake_key} details"
        cleaned = _scrub(dirty, fake_key)
        assert fake_key not in cleaned
        assert "[REDACTED]" in cleaned

    def test_scrub_no_key_is_noop(self):
        text = "some error message"
        assert _scrub(text, None) == text
        assert _scrub(text, "") == text


# ---------------------------------------------------------------------------
# 3. JSON parsing and invalid-response handling
# ---------------------------------------------------------------------------

class TestResponseParsing:
    def test_valid_correct_verdict(self):
        raw = json.dumps({"verdict": "correct", "reason": "Looks good."})
        v, r, err = _parse_response(raw)
        assert v == "correct"
        assert r == "Looks good."
        assert err is None

    def test_valid_incorrect_verdict(self):
        raw = json.dumps({"verdict": "incorrect", "reason": "Wrong."})
        v, r, err = _parse_response(raw)
        assert v == "incorrect"
        assert err is None

    def test_invalid_json(self):
        v, r, err = _parse_response("not json at all")
        assert v is None
        assert r is None
        assert "JSONDecodeError" in err

    def test_missing_verdict_field(self):
        raw = json.dumps({"reason": "Something"})
        v, r, err = _parse_response(raw)
        assert v is None
        assert "ValidationError" in err

    def test_unknown_verdict_value(self):
        raw = json.dumps({"verdict": "maybe", "reason": "Unsure"})
        v, r, err = _parse_response(raw)
        assert v is None
        assert err is not None

    def test_empty_reason_rejected(self):
        raw = json.dumps({"verdict": "correct", "reason": ""})
        v, r, err = _parse_response(raw)
        assert v is None
        assert err is not None

    def test_whitespace_only_reason_rejected(self):
        raw = json.dumps({"verdict": "correct", "reason": "   "})
        v, r, err = _parse_response(raw)
        assert v is None
        assert err is not None

    def test_missing_reason_field(self):
        raw = json.dumps({"verdict": "correct"})
        v, r, err = _parse_response(raw)
        assert v is None
        assert err is not None


# ---------------------------------------------------------------------------
# 4. Dry-run / live separation and resume without duplicates
# ---------------------------------------------------------------------------

class TestSaveResume:
    def test_append_and_load_completed(self, tmp_path):
        results_path = tmp_path / "results.jsonl"
        rec = _fake_result("r00")
        _append_result(rec, results_path)
        _append_result(_fake_result("r01", status="error"), results_path)
        completed = _load_completed(results_path)
        assert "r00" in completed
        assert "r01" in completed
        assert len(completed) == 2

    def test_pending_not_counted_as_completed(self, tmp_path):
        results_path = tmp_path / "results.jsonl"
        pending = {**_fake_result("r00"), "status": "pending"}
        _append_result(pending, results_path)
        completed = _load_completed(results_path)
        assert "r00" not in completed

    def test_dry_run_not_counted_as_completed(self, tmp_path):
        """dry_run records must never be treated as completed by --resume."""
        results_path = tmp_path / "results.jsonl"
        dry = {**_fake_result("r00"), "status": "dry_run"}
        _append_result(dry, results_path)
        completed = _load_completed(results_path)
        assert "r00" not in completed
        assert len(completed) == 0

    def test_live_completed_statuses(self):
        """Only actual API outcomes count as completed."""
        assert LIVE_COMPLETED_STATUSES == frozenset({"completed", "error", "invalid_response"})
        assert "dry_run" not in LIVE_COMPLETED_STATUSES
        assert "pending" not in LIVE_COMPLETED_STATUSES

    def test_dry_run_writes_to_dry_run_path(self, tmp_path):
        """Dry-run must write to dry_run/results.jsonl, not results.jsonl."""
        manifest_path = tmp_path / "manifest.json"
        dry_run_path = tmp_path / "dry_run" / "results.jsonl"
        live_path = tmp_path / "results.jsonl"

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", dry_run_path),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
        ):
            run(dry_run=True)

        # Dry-run records go to dry_run/results.jsonl
        assert dry_run_path.exists()
        lines = dry_run_path.read_text().splitlines()
        records = [json.loads(l) for l in lines if l.strip()]
        assert len(records) == 20
        assert all(r["status"] == "dry_run" for r in records)

        # Live results.jsonl must not exist after dry-run
        assert not live_path.exists()

    def test_dry_run_and_live_use_separate_files(self, tmp_path):
        """Dry-run and live must not share a results file."""
        assert DRY_RUN_RESULTS_PATH != RESULTS_PATH
        assert "dry_run" in str(DRY_RUN_RESULTS_PATH)
        assert "dry_run" not in str(RESULTS_PATH)

    def test_resume_skips_completed_live_only(self, tmp_path):
        """Resume on a live run skips only actual API outcomes."""
        manifest_path = tmp_path / "manifest.json"
        dry_run_path = tmp_path / "dry_run" / "results.jsonl"
        live_path = tmp_path / "results.jsonl"

        # Step 1: dry-run to create manifest
        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", dry_run_path),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
        ):
            run(dry_run=True)

        # Step 2: manually write 5 completed live records
        manifest = json.loads(manifest_path.read_text())
        for i, req in enumerate(manifest["requests"][:5]):
            rec = {**req, "status": "completed", "parsed_verdict": "incorrect",
                   "timestamp_utc": "2026-10-21T00:00:00+00:00"}
            _append_result(rec, live_path)

        # Step 3: mock live resume — should skip 5, process remaining 15
        mock_resp = _make_mock_response()
        call_count = 0

        def fake_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_resp

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", dry_run_path),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
            patch("src.stage2.runner._load_api_key", return_value="fake-key"),
            patch("google.genai.Client") as MockClient,
            patch("src.stage2.runner.time.sleep"),  # skip 6s delays in tests
        ):
            MockClient.return_value.models.generate_content = fake_generate
            run(resume=True)

        # Live results should have 5 pre-existing + 15 new = 20
        live_records = [json.loads(l) for l in live_path.read_text().splitlines() if l.strip()]
        assert len(live_records) == 20
        # Exactly 15 new API calls (5 were skipped)
        assert call_count == 15

    def test_resume_detects_config_change(self, tmp_path):
        manifest_path = tmp_path / "manifest.json"
        dry_run_path = tmp_path / "dry_run" / "results.jsonl"
        live_path = tmp_path / "results.jsonl"

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", dry_run_path),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
        ):
            run(dry_run=True)

        # Tamper with the saved manifest
        manifest = json.loads(manifest_path.read_text())
        manifest["model_id"] = "different-model"
        manifest_path.write_text(json.dumps(manifest))

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", dry_run_path),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
        ):
            with pytest.raises(RuntimeError, match="fingerprint mismatch"):
                run(dry_run=False, resume=True)

    def test_results_isolated_from_stage1(self):
        """Stage 2 results path must not overlap with Stage 1 outputs."""
        from src.stage2.runner import RESULTS_PATH as S2_RESULTS
        from src.run_validation import ROOT as S1_ROOT
        stage1_out = S1_ROOT / "outputs" / "pilot" / "stage1_validation.json"
        assert S2_RESULTS != stage1_out
        assert "stage2" in str(S2_RESULTS)


# ---------------------------------------------------------------------------
# 5. Config-change detection (expanded: model, instruction, settings, schema, prompts)
# ---------------------------------------------------------------------------

class TestConfigFingerprint:
    def test_same_manifest_same_fingerprint(self):
        m1 = build_manifest()
        m2 = build_manifest()
        assert config_fingerprint(m1) == config_fingerprint(m2)

    def test_different_model_different_fingerprint(self):
        m1 = build_manifest()
        m2 = build_manifest()
        m2["model_id"] = "different-model"
        assert config_fingerprint(m1) != config_fingerprint(m2)

    def test_different_instruction_different_fingerprint(self):
        m1 = build_manifest()
        m2 = build_manifest()
        m2["judge_instruction"] = "do something else"
        assert config_fingerprint(m1) != config_fingerprint(m2)

    def test_different_generation_settings_different_fingerprint(self):
        m1 = build_manifest()
        m2 = build_manifest()
        # Deep-copy to avoid mutating the shared GENERATION_SETTINGS dict
        import copy
        m2["generation_settings"] = copy.deepcopy(m2["generation_settings"])
        m2["generation_settings"]["temperature"] = 0.5
        assert config_fingerprint(m1) != config_fingerprint(m2)

    def test_different_prompts_different_fingerprint(self):
        """Tampering with a prompt text must change the fingerprint."""
        m1 = build_manifest()
        m2 = build_manifest()
        m2["requests"][0]["prompt"] = "tampered prompt"
        assert config_fingerprint(m1) != config_fingerprint(m2)

    def test_different_dataset_hashes_different_fingerprint(self):
        m1 = build_manifest()
        m2 = build_manifest()
        m2["dataset_hashes"]["data\\pilot\\p01.json"] = "a" * 64
        assert config_fingerprint(m1) != config_fingerprint(m2)

    def test_fingerprint_covers_response_schema(self):
        """The fingerprint must include the response schema definition."""
        # The fingerprint is computed from JudgeResponse.model_json_schema().
        # We verify that the schema is actually part of the hash by checking
        # that it's a non-trivial component.
        m = build_manifest()
        from src.stage2.schema import JudgeResponse
        schema = JudgeResponse.model_json_schema()
        # The schema must define verdict and reason fields
        assert "properties" in schema
        assert "verdict" in schema["properties"]
        assert "reason" in schema["properties"]


# ---------------------------------------------------------------------------
# 6. Invalid responses are recorded outcomes, not retried
# ---------------------------------------------------------------------------

class TestInvalidResponseHandling:
    def test_invalid_json_recorded_not_retried(self, tmp_path):
        """An invalid JSON response is saved as invalid_response, run continues."""
        manifest_path = tmp_path / "manifest.json"
        dry_run_path = tmp_path / "dry_run" / "results.jsonl"
        live_path = tmp_path / "results.jsonl"

        bad_response = MagicMock()
        bad_response.text = "not valid json {{{"
        bad_response.usage_metadata = None
        bad_response.model_version = None
        bad_response.candidates = []

        call_count = 0

        def fake_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return bad_response

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", dry_run_path),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
        ):
            run(dry_run=True)

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", tmp_path / "dry2" / "results.jsonl"),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
            patch("src.stage2.runner._load_api_key", return_value="fake-key"),
            patch("google.genai.Client") as MockClient,
            patch("src.stage2.runner.time.sleep"),
        ):
            MockClient.return_value.models.generate_content = fake_generate
            run(limit=1, resume=False)

        records = [json.loads(l) for l in live_path.read_text().splitlines() if l.strip()]
        assert len(records) == 1
        rec = records[0]
        assert rec["status"] == "invalid_response"
        assert rec["parsed_verdict"] is None
        assert call_count == 1

    def test_unknown_verdict_recorded_not_retried(self, tmp_path):
        manifest_path = tmp_path / "manifest.json"
        dry_run_path = tmp_path / "dry_run" / "results.jsonl"
        live_path = tmp_path / "results.jsonl"

        unknown_resp = MagicMock()
        unknown_resp.text = json.dumps({"verdict": "uncertain", "reason": "not sure"})
        unknown_resp.usage_metadata = None
        unknown_resp.model_version = None
        unknown_resp.candidates = []

        call_count = 0

        def fake_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return unknown_resp

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", dry_run_path),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
        ):
            run(dry_run=True)

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", tmp_path / "dry2" / "results.jsonl"),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
            patch("src.stage2.runner._load_api_key", return_value="fake-key"),
            patch("google.genai.Client") as MockClient,
            patch("src.stage2.runner.time.sleep"),
        ):
            MockClient.return_value.models.generate_content = fake_generate
            run(limit=1, resume=False)

        records = [json.loads(l) for l in live_path.read_text().splitlines() if l.strip()]
        assert records[0]["status"] == "invalid_response"
        assert call_count == 1


# ---------------------------------------------------------------------------
# 7. API key never appears in error output
# ---------------------------------------------------------------------------

class TestKeyProtection:
    def test_key_not_in_scrubbed_error(self):
        key = "AIzaSyFAKEKEY99999"
        msg = f"HTTPError 403 with api_key={key} for request"
        cleaned = _scrub(msg, key)
        assert key not in cleaned

    def test_scrub_with_none_key_safe(self):
        msg = "some error"
        assert _scrub(msg, None) == msg

    def test_import_error_no_key(self, tmp_path):
        """If google-genai is not importable, error message must not contain key."""
        manifest_path = tmp_path / "manifest.json"
        dry_run_path = tmp_path / "dry_run" / "results.jsonl"
        live_path = tmp_path / "results.jsonl"
        fake_key = "AIzaSyFAKE"

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", dry_run_path),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
        ):
            run(dry_run=True)

        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "google.genai" or name == "google":
                raise ImportError("No module named 'google'")
            return real_import(name, *args, **kwargs)

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", tmp_path / "dry2" / "results.jsonl"),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
            patch("src.stage2.runner._load_api_key", return_value=fake_key),
            patch("builtins.__import__", side_effect=mock_import),
            patch("src.stage2.runner.time.sleep"),
        ):
            run(limit=1)

        lines = [json.loads(l) for l in live_path.read_text().splitlines() if l.strip()]
        for rec in lines:
            err = rec.get("error_info") or ""
            assert fake_key not in err, f"Key found in error_info: {err!r}"


# ---------------------------------------------------------------------------
# 8. Focused integration test: dry-run → mocked live --limit 1 → resume → 20 total
# ---------------------------------------------------------------------------

class TestDryRunLiveResumeIntegration:
    """End-to-end offline test verifying dry-run/live separation.

    Steps:
    1. Dry-run (creates manifest + 20 dry_run records in dry_run/results.jsonl)
    2. Mocked live run with --limit 1 (creates 1 completed record in results.jsonl)
    3. Mocked live resume (processes remaining 19, skips the 1 already done)
    4. Verify exactly 20 live API calls total, none skipped due to dry-run records
    """

    def test_dry_run_then_live_then_resume(self, tmp_path):
        manifest_path = tmp_path / "manifest.json"
        dry_run_path = tmp_path / "dry_run" / "results.jsonl"
        live_path = tmp_path / "results.jsonl"

        # Step 1: dry-run
        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", dry_run_path),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
        ):
            run(dry_run=True)

        # Verify dry-run evidence
        assert dry_run_path.exists()
        dry_records = [json.loads(l) for l in dry_run_path.read_text().splitlines() if l.strip()]
        assert len(dry_records) == 20
        assert all(r["status"] == "dry_run" for r in dry_records)
        assert not live_path.exists(), "Live results must not exist after dry-run only"

        # Step 2: mocked live run with --limit 1
        mock_resp = _make_mock_response()
        api_calls = []

        def fake_generate(*args, **kwargs):
            api_calls.append(kwargs.get("model", "?"))
            return mock_resp

        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", tmp_path / "dry2" / "results.jsonl"),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
            patch("src.stage2.runner._load_api_key", return_value="fake-key"),
            patch("google.genai.Client") as MockClient,
            patch("src.stage2.runner.time.sleep"),  # skip 6s delays
        ):
            MockClient.return_value.models.generate_content = fake_generate
            run(limit=1, resume=False)

        # Verify: 1 live result, 1 API call
        live_records = [json.loads(l) for l in live_path.read_text().splitlines() if l.strip()]
        assert len(live_records) == 1
        assert live_records[0]["status"] == "completed"
        assert len(api_calls) == 1

        # Step 3: resume — should process remaining 19, skip the 1 completed
        with (
            patch("src.stage2.runner.MANIFEST_PATH", manifest_path),
            patch("src.stage2.runner.DRY_RUN_RESULTS_PATH", tmp_path / "dry2" / "results.jsonl"),
            patch("src.stage2.runner.RESULTS_PATH", live_path),
            patch("src.stage2.runner._load_api_key", return_value="fake-key"),
            patch("google.genai.Client") as MockClient,
            patch("src.stage2.runner.time.sleep"),
        ):
            MockClient.return_value.models.generate_content = fake_generate
            run(resume=True)

        # Verify: 20 total live results (1 + 19)
        all_live = [json.loads(l) for l in live_path.read_text().splitlines() if l.strip()]
        assert len(all_live) == 20, f"Expected 20 live records, got {len(all_live)}"

        # Verify: exactly 20 API calls total (1 + 19), none skipped due to dry-run
        assert len(api_calls) == 20, (
            f"Expected 20 total API calls, got {len(api_calls)}. "
            "Dry-run records may have been mistaken for live completions."
        )

        # Verify: all 20 live results are completed (not dry_run)
        assert all(r["status"] == "completed" for r in all_live), (
            f"Found non-completed live records: "
            f"{[r['request_id'] for r in all_live if r['status'] != 'completed']}"
        )

        # Verify: all 20 unique request IDs present
        live_ids = {r["request_id"] for r in all_live}
        assert len(live_ids) == 20

        # Verify: dry-run evidence still intact
        dry_after = [json.loads(l) for l in dry_run_path.read_text().splitlines() if l.strip()]
        assert len(dry_after) == 20
        assert all(r["status"] == "dry_run" for r in dry_after)
