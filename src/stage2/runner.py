"""Stage 2 API runner.

Sends the 20 experimental requests to the Gemini API, saves each result
immediately, and supports --dry-run, --limit and --resume.

Nothing in this module prints, logs or includes the API key.
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# google-genai is imported lazily so dry-run works without the package installed.

from src.stage2.schema import JudgeResponse, RequestRecord, Verdict
from src.stage2.experiment import (
    MODEL_ID,
    JUDGE_INSTRUCTION,
    GENERATION_SETTINGS,
    build_manifest,
    config_fingerprint,
    load_manifest,
    save_manifest,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]  # src/stage2/ -> src/ -> project root
OUTPUTS_DIR = ROOT / "outputs" / "pilot" / "stage2"
MANIFEST_PATH = OUTPUTS_DIR / "manifest.json"
RESULTS_PATH = OUTPUTS_DIR / "results.jsonl"                 # live results only
DRY_RUN_RESULTS_PATH = OUTPUTS_DIR / "dry_run" / "results.jsonl"  # dry-run evidence

# Statuses that count as completed for --resume (actual API outcomes only).
# "dry_run" is NOT in this set — it must never be treated as a live result.
LIVE_COMPLETED_STATUSES = frozenset({"completed", "error", "invalid_response"})


# ---------------------------------------------------------------------------
# API key – read from environment or .env; never echoed
# ---------------------------------------------------------------------------

def _load_api_key() -> str:
    """Return the API key from env or .env file.  Raises if absent."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key

    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == "GEMINI_API_KEY":
                key = v.strip().strip('"').strip("'")
                if key:
                    return key

    raise EnvironmentError(
        "GEMINI_API_KEY not found in environment or .env file. "
        "Copy .env.example to .env and fill in your key."
    )


# ---------------------------------------------------------------------------
# Key-scrubbing helper – prevents accidental key leakage in error strings
# ---------------------------------------------------------------------------

def _scrub(text: str, api_key: Optional[str]) -> str:
    if api_key and api_key in text:
        return text.replace(api_key, "[REDACTED]")
    return text


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_response(raw: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (verdict, reason, error_info).

    Parses the raw text as JSON and validates against JudgeResponse.
    Returns (None, None, error_info) for any parse/validation failure.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, None, f"JSONDecodeError: {exc}"

    try:
        parsed = JudgeResponse.model_validate(data)
        return parsed.verdict.value, parsed.reason, None
    except Exception as exc:
        return None, None, f"ValidationError: {exc}"


# ---------------------------------------------------------------------------
# Completed-request index
# ---------------------------------------------------------------------------

def _load_completed(results_path: Path) -> dict[str, dict]:
    """Return {request_id: record} for every live-completed line.

    Only actual API outcomes (completed, error, invalid_response) count.
    dry_run records are never treated as completed.
    """
    completed: dict[str, dict] = {}
    if not results_path.exists():
        return completed
    for line in results_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("status") in LIVE_COMPLETED_STATUSES:
            completed[rec["request_id"]] = rec
    return completed


# ---------------------------------------------------------------------------
# Single request attempt
# ---------------------------------------------------------------------------

def _attempt(
    req: RequestRecord,
    api_key: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Execute one API request and return a result dict.

    On dry_run, returns a synthetic record with no network call.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if dry_run:
        return {
            **req.model_dump(),
            "status": "dry_run",
            "timestamp_utc": timestamp,
            "raw_response": None,
            "parsed_verdict": None,
            "parsed_reason": None,
            "returned_model_version": None,
            "usage_metadata": None,
            "error_info": None,
            "retry_count": 0,
        }

    # --- real call ---
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        return {
            **req.model_dump(),
            "status": "error",
            "timestamp_utc": timestamp,
            "error_info": f"ImportError: {exc} — run: pip install google-genai",
            "retry_count": 0,
        }

    # Generation config (omit None values for top_p / top_k)
    gen_settings = {k: v for k, v in GENERATION_SETTINGS.items() if v is not None}

    # Disable SDK-level automatic retries.  The SDK defaults to 5 attempts
    # with exponential backoff; if left enabled, our own retry loop would
    # multiply invisibly (up to 5 x 4 = 20 attempts per request).  We handle
    # all retry logic ourselves with explicit counting and 6-second spacing.
    config = types.GenerateContentConfig(
        system_instruction=JUDGE_INSTRUCTION,
        temperature=gen_settings.get("temperature", 0.0),
        max_output_tokens=gen_settings.get("max_output_tokens", 256),
        candidate_count=gen_settings.get("candidate_count", 1),
        response_mime_type="application/json",
        response_schema=JudgeResponse,
        http_options=types.HttpOptions(
            timeout=60_000,  # 60 seconds in ms
            retry_options=types.HttpRetryOptions(attempts=1),  # no SDK retries
        ),
    )

    retry_count = 0
    max_retries = 3
    retry_delay = 6.0  # seconds; also used as min spacing between requests

    while True:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=req.prompt,
                config=config,
            )

            raw = response.text or ""

            # Collect usage metadata safely
            usage: Optional[dict] = None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                um = response.usage_metadata
                usage = {
                    "prompt_token_count": getattr(um, "prompt_token_count", None),
                    "candidates_token_count": getattr(um, "candidates_token_count", None),
                    "total_token_count": getattr(um, "total_token_count", None),
                }

            # Model version
            returned_model = None
            if hasattr(response, "model_version"):
                returned_model = response.model_version
            elif (hasattr(response, "candidates") and response.candidates
                  and hasattr(response.candidates[0], "model_version")):
                returned_model = response.candidates[0].model_version

            verdict, reason, parse_error = _parse_response(raw)

            if parse_error:
                # Invalid response: record it, do NOT retry for a different answer.
                return {
                    **req.model_dump(),
                    "status": "invalid_response",
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "raw_response": raw,
                    "parsed_verdict": None,
                    "parsed_reason": None,
                    "returned_model_version": returned_model,
                    "usage_metadata": usage,
                    "error_info": parse_error,
                    "retry_count": retry_count,
                }

            return {
                **req.model_dump(),
                "status": "completed",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "raw_response": raw,
                "parsed_verdict": verdict,
                "parsed_reason": reason,
                "returned_model_version": returned_model,
                "usage_metadata": usage,
                "error_info": None,
                "retry_count": retry_count,
            }

        except Exception as exc:  # noqa: BLE001
            err_str = _scrub(str(exc), api_key)
            err_type = type(exc).__name__

            # --- classify the error ---

            # Exhausted daily quota: do not retry, stop the run.
            if _is_quota_exhausted(err_str, exc):
                return {
                    **req.model_dump(),
                    "status": "error",
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "error_info": f"QuotaExhausted: {err_str}",
                    "retry_count": retry_count,
                }, "quota_exhausted"  # type: ignore[return-value]

            # Refusal / content policy: record, do not retry.
            if _is_refusal(err_str, exc):
                return {
                    **req.model_dump(),
                    "status": "error",
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "error_info": f"Refusal: {err_str}",
                    "retry_count": retry_count,
                }

            # Temporary error: retry with back-off, respecting Retry-After.
            if retry_count < max_retries and _is_retryable(err_str, exc):
                retry_after = _parse_retry_after(err_str)
                wait = max(retry_after, retry_delay * (2 ** retry_count))
                retry_count += 1
                time.sleep(wait)
                continue

            # Non-retryable or retries exhausted.
            return {
                **req.model_dump(),
                "status": "error",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "error_info": f"{err_type}: {err_str}",
                "retry_count": retry_count,
            }


def _is_retryable(err_str: str, exc: Exception) -> bool:
    s = err_str.lower()
    return any(x in s for x in ("429", "503", "timeout", "unavailable", "resource_exhausted"))


def _is_quota_exhausted(err_str: str, exc: Exception) -> bool:
    """Daily quota exhausted (distinct from per-minute rate limit)."""
    s = err_str.lower()
    return "quota_exceeded" in s or (
        "resource_exhausted" in s and "daily" in s
    )


def _is_refusal(err_str: str, exc: Exception) -> bool:
    s = err_str.lower()
    return any(x in s for x in ("finish_reason: safety", "blocked", "harm_category"))


def _parse_retry_after(err_str: str) -> float:
    """Extract a Retry-After value in seconds if present, else 0."""
    m = re.search(r"retry.after[:\s]+(\d+)", err_str, re.IGNORECASE)
    return float(m.group(1)) if m else 0.0


# ---------------------------------------------------------------------------
# Result persistence
# ---------------------------------------------------------------------------

def _append_result(result: dict, results_path: Path) -> None:
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(result) + "\n")


# ---------------------------------------------------------------------------
# Main run loop
# ---------------------------------------------------------------------------

def run(
    *,
    dry_run: bool = False,
    limit: Optional[int] = None,
    resume: bool = False,
) -> None:
    """Execute the experiment.

    dry_run  – no API key required; zero network calls.
               Results saved to outputs/pilot/stage2/dry_run/results.jsonl
    limit    – stop after this many requests (useful for a single live test).
    resume   – skip already-completed requests; refuse if config changed.
               Only actual API outcomes in results.jsonl are counted;
               dry_run records are never treated as completed.
    """
    # --- prepare manifest ---
    if resume and MANIFEST_PATH.exists():
        manifest = load_manifest(MANIFEST_PATH)
        # Verify config hasn't changed.
        current_fp = config_fingerprint(build_manifest())
        saved_fp = config_fingerprint(manifest)
        if current_fp != saved_fp:
            raise RuntimeError(
                "Manifest config fingerprint mismatch. "
                "Dataset, prompts, model or settings have changed since the "
                "manifest was saved. Delete the manifest to start fresh."
            )
        print(f"Resuming from existing manifest: {MANIFEST_PATH}")
    else:
        manifest = build_manifest()
        save_manifest(manifest, MANIFEST_PATH)
        print(f"Manifest saved: {MANIFEST_PATH}")

    # --- choose results path ---
    # Dry-run evidence is stored separately from live results so that
    # --resume never mistakes dry_run records for completed API calls.
    results_path = DRY_RUN_RESULTS_PATH if dry_run else RESULTS_PATH

    requests = manifest["requests"]

    # When resuming a live run, load completed records from the live file.
    # Dry-run never resumes (it regenerates all 20 records each time).
    completed = _load_completed(results_path) if (resume and not dry_run) else {}

    if dry_run:
        print("DRY RUN — no API key required, zero network calls.")
        api_key = None
    else:
        api_key = _load_api_key()

    run_count = 0
    stop_reason = None

    for req_dict in requests:
        req_id = req_dict["request_id"]

        # Skip completed requests when resuming (live only).
        if resume and not dry_run and req_id in completed:
            print(f"  {req_id} — skipped (already completed)")
            continue

        if limit is not None and run_count >= limit:
            print(f"Reached --limit {limit}; stopping.")
            break

        req = RequestRecord(**req_dict)
        print(
            f"  {req_id} — {req.problem_id} / {req.candidate} / "
            f"condition {req.condition}",
            end=" ... ",
            flush=True,
        )

        result = _attempt(req, api_key, dry_run=dry_run)

        # _attempt may return a (dict, "quota_exhausted") tuple on daily quota.
        if isinstance(result, tuple):
            result, stop_reason = result
            _append_result(result, results_path)
            print(f"QUOTA EXHAUSTED — {result.get('error_info', '')}")
            break

        _append_result(result, results_path)
        run_count += 1

        status = result.get("status", "?")
        verdict = result.get("parsed_verdict") or ""
        print(f"{status}" + (f" ({verdict})" if verdict else ""))

        # Minimum 6-second spacing between every live attempt
        # (not just between requests, but our retry backoff also starts at 6s).
        # Dry-run skips the delay.
        if not dry_run:
            time.sleep(6)

    print(
        f"\nDone. {run_count} request(s) attempted. "
        f"Results: {results_path}"
    )
    if stop_reason == "quota_exhausted":
        print("WARNING: daily quota exhausted. Resume tomorrow with --resume.")
