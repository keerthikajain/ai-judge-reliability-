"""Pydantic models for structured API request/response and result persistence."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Judge response schema – sent to the API as response_schema
# ---------------------------------------------------------------------------

class Verdict(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"


class JudgeResponse(BaseModel):
    verdict: Verdict
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("reason must not be empty")
        return v


# ---------------------------------------------------------------------------
# One experimental request record (manifest + result combined)
# ---------------------------------------------------------------------------

class RequestRecord(BaseModel):
    """Everything about one of the 20 scheduled requests.

    Fields populated at manifest creation time are always present.
    Fields populated after the API call are Optional so the manifest can be
    saved before any calls are made.
    """

    # --- identity ---
    request_id: str          # e.g. "r00" … "r19" (post-shuffle ordinal)
    problem_id: str          # e.g. "p01"
    candidate: str           # "reference_solution" or "faulty_solution"
    condition: str           # "A" or "B"

    # --- prompt ---
    prompt: str              # exact text sent to the model

    # --- result (None until the request completes) ---
    status: str = "pending"  # "pending" | "completed" | "error" | "invalid_response"
    timestamp_utc: Optional[str] = None
    raw_response: Optional[str] = None
    parsed_verdict: Optional[str] = None   # "correct" | "incorrect" | None
    parsed_reason: Optional[str] = None
    returned_model_version: Optional[str] = None
    usage_metadata: Optional[dict] = None
    error_info: Optional[str] = None       # never contains the API key
    retry_count: int = 0
