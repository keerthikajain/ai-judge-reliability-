"""Build and shuffle the 120-request main-study experiment manifest.

Reuses the pilot's MODEL_ID, JUDGE_INSTRUCTION, GENERATION_SETTINGS,
CANDIDATES, CONDITIONS and response schema unchanged.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

from src.prompts import build_prompt
from src.main_validation import ROOT, load_main_tasks
from src.stage2.schema import RequestRecord
from src.stage2.experiment import (
    MODEL_ID,
    JUDGE_INSTRUCTION,
    GENERATION_SETTINGS,
    CANDIDATES,
    CONDITIONS,
    _sdk_version,
)

# Separate seed for the main study (distinct from pilot's 20261021).
MAIN_SHUFFLE_SEED = 20261022


def _dataset_hash() -> dict[str, str]:
    """SHA-256 of every file in data/main/ (sorted by name)."""
    main_dir = ROOT / "data" / "main"
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(main_dir.glob("*.json"))
    }


def build_main_manifest() -> dict[str, Any]:
    """Return the full 120-request manifest dict (shuffled, no API key)."""
    tasks = load_main_tasks()

    requests: list[RequestRecord] = []
    for problem in tasks:
        for candidate in CANDIDATES:
            code = problem[candidate]
            for condition in CONDITIONS:
                include_claim = condition == "B"
                prompt = build_prompt(
                    problem_statement=problem["problem_statement"],
                    candidate_code=code,
                    include_claim=include_claim,
                )
                requests.append(RequestRecord(
                    request_id="",
                    problem_id=problem["id"],
                    candidate=candidate,
                    condition=condition,
                    prompt=prompt,
                ))

    assert len(requests) == 120, f"Expected 120 requests, got {len(requests)}"

    rng = random.Random(MAIN_SHUFFLE_SEED)
    rng.shuffle(requests)

    for i, req in enumerate(requests):
        req.request_id = f"r{i:03d}"

    # Verify no private metadata leaked into any prompt
    private_fields = {"bug_explanation", "named_counterexample",
                      "human_review_status", "provenance", "split",
                      "reference_solution", "faulty_solution"}
    for req in requests:
        for field in private_fields:
            assert field not in req.prompt, (
                f"Private field '{field}' found in prompt for {req.request_id}"
            )

    return {
        "stage": "main_study",
        "model_id": MODEL_ID,
        "judge_instruction": JUDGE_INSTRUCTION,
        "generation_settings": GENERATION_SETTINGS,
        "shuffle_seed": MAIN_SHUFFLE_SEED,
        "sdk_version": _sdk_version(),
        "dataset_hashes": _dataset_hash(),
        "total_requests": len(requests),
        "requests": [r.model_dump() for r in requests],
    }


def config_fingerprint(manifest: dict[str, Any]) -> str:
    """A stable hash of every field that must not change mid-run."""
    from src.stage2.schema import JudgeResponse

    schema_json = json.dumps(
        JudgeResponse.model_json_schema(), sort_keys=True
    )
    prompt_hashes = sorted(
        hashlib.sha256(r["prompt"].encode()).hexdigest()
        for r in manifest["requests"]
    )

    key = {
        "model_id": manifest["model_id"],
        "judge_instruction": manifest["judge_instruction"],
        "generation_settings": manifest["generation_settings"],
        "shuffle_seed": manifest["shuffle_seed"],
        "dataset_hashes": manifest["dataset_hashes"],
        "response_schema_hash": hashlib.sha256(schema_json.encode()).hexdigest(),
        "prompt_hashes": prompt_hashes,
    }
    return hashlib.sha256(
        json.dumps(key, sort_keys=True).encode()
    ).hexdigest()


def save_manifest(manifest: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
