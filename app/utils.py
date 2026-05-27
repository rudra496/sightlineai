from __future__ import annotations

import json
import re
from typing import Any

from app.schemas import GuidanceResponse

JSON_BLOCK_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


def extract_json_object(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("Model returned an empty response")

    stripped = text.strip()

    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    match = JSON_BLOCK_PATTERN.search(stripped)
    if not match:
        raise ValueError("Unable to parse JSON from model response")

    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError("Model response contained invalid JSON") from exc

    if not isinstance(obj, dict):
        raise ValueError("Model JSON response is not an object")

    return obj


def normalize_guidance_payload(payload: dict[str, Any]) -> GuidanceResponse:
    def _clean(value: Any, fallback: str) -> str:
        if isinstance(value, str):
            clean_value = value.strip()
            if clean_value:
                return clean_value
        return fallback

    return GuidanceResponse(
        guidance_text=_clean(
            payload.get("guidance_text"),
            "I could not confidently interpret the scene. Please provide more detail.",
        ),
        safety_notes=_clean(
            payload.get("safety_notes"),
            "Stay cautious, move slowly, and verify surroundings before each step.",
        ),
        confidence_notes=_clean(
            payload.get("confidence_notes"),
            "Low confidence due to limited scene details.",
        ),
        mode="qwen",
    )
