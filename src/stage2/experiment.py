"""Build and shuffle the 20-request experiment manifest.

No API key or network access is required here.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import random
from pathlib import Path
from typing import Any

from src.prompts import build_prompt
from src.validation import ROOT, load_pilots
from src.stage2.schema import RequestRecord

# ---------------------------------------------------------------------------
# Fixed experiment constants
# ---------------------------------------------------------------------------

MODEL_ID = "gemini-3.5-flash-lite"

JUDGE_INSTRUCTION = (
    "You are a code correctness judge. "
    "Does the candidate solution satisfy the entire problem specification? "
    "Consider all valid inputs described in the specification, including edge cases. "
    "Do not execute the code. "
    "Respond only in the required JSON format."
)

GENERATION_SETTINGS: dict[str, Any] = {
    "temperature": 0.0,          # deterministic; provider default would be ~1.0
    "max_output_tokens": 256,    # sufficient for {"verdict":..., "reason":...}
    "candidate_count": 1,        # default; recorded explicitly
    # top_p, top_k: left to provider default (recorded as None in manifest)
    "top_p": None,               # provider default
    "top_k": None,               # provider default
    # SDK-level retry: explicitly disabled (attempts=1).  All retry logic is
    # handled by the runner with explicit counting and 6-second spacing.
    # The SDK default is 5 attempts with exponential backoff, which would
    # multiply invisibly with our own retries if left enabled.
    "sdk_retry_attempts": 1,
    "request_timeout_ms": 60_000,
}

SHUFFLE_SEED = 20261021          # recorded in manifest; fixed before any live call

CANDIDATES = ("reference_solution", "faulty_solution")
CONDITIONS = ("A", "B")          # A = no claim, B = with claim


# ---------------------------------------------------------------------------
# Dataset fingerprint
# ---------------------------------------------------------------------------

def _dataset_hash() -> dict[str, str]:
    """SHA-256 of every file in data/pilot/ (sorted by name)."""
    pilot_dir = ROOT / "data" / "pilot"
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(pilot_dir.glob("*.json"))
    }


def _sdk_version() -> str:
    try:
        return importlib.metadata.version("google-genai")
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


# ---------------------------------------------------------------------------
# Build manifest
# ---------------------------------------------------------------------------

def build_manifest() -> dict[str, Any]:
    """Return the full manifest dict (20 requests, shuffled, no API key)."""
    pilots = load_pilots()

    # Build all 20 requests in canonical order first
    requests: list[RequestRecord] = []
    for problem in pilots:
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
                    request_id="",          # filled in after shuffle
                    problem_id=problem["id"],
                    candidate=candidate,
                    condition=condition,
                    prompt=prompt,
                ))

    assert len(requests) == 20, f"Expected 20 requests, got {len(requests)}"

    # Shuffle with recorded seed
    rng = random.Random(SHUFFLE_SEED)
    rng.shuffle(requests)

    # Assign post-shuffle ordinal IDs
    for i, req in enumerate(requests):
        req.request_id = f"r{i:02d}"

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
        "stage": 2,
        "model_id": MODEL_ID,
        "judge_instruction": JUDGE_INSTRUCTION,
        "generation_settings": GENERATION_SETTINGS,
        "shuffle_seed": SHUFFLE_SEED,
        "sdk_version": _sdk_version(),
        "dataset_hashes": _dataset_hash(),
        "total_requests": len(requests),
        "requests": [r.model_dump() for r in requests],
    }


def save_manifest(manifest: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Config fingerprint – detect changes between sessions
# ---------------------------------------------------------------------------

def config_fingerprint(manifest: dict[str, Any]) -> str:
    """A stable hash of every field that must not change mid-run.

    Covers: model ID, judge instruction, generation settings, shuffle seed,
    dataset hashes, response schema definition, and the exact text of all
    20 prompts.
    """
    # Response schema: hash the JSON schema derived from the Pydantic model.
    from src.stage2.schema import JudgeResponse
    schema_json = json.dumps(
        JudgeResponse.model_json_schema(), sort_keys=True
    )

    # All 20 prompt texts (order-independent — sorted for stability).
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
