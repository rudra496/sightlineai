from __future__ import annotations

import json
import re
from typing import Any

from app.schemas import GuidanceResponse

JSON_BLOCK_PATTERN = re.compile(r"\{.*\}", re.DOTALL)
MARKDOWN_JSON_PATTERN = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)

# Minimum character thresholds for quality validation.
MIN_GUIDANCE_LENGTH = 15
MIN_SAFETY_LENGTH = 10


def extract_json_from_markdown(text: str) -> str | None:
    """Extract JSON from ```json...``` code blocks in model output.

    Returns the extracted content (without backticks), or None if no block found.
    """
    match = MARKDOWN_JSON_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return None


def extract_json_object(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("Model returned an empty response")

    stripped = text.strip()

    # Try direct JSON parse first.
    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block.
    md_content = extract_json_from_markdown(stripped)
    if md_content:
        try:
            obj = json.loads(md_content)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    # Fall back to finding first {…} block.
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
    """Normalize both nested and flat payload structures into a GuidanceResponse.

    Handles cases where the model returns nested guidance (e.g. {"response": {"guidance_text": ...}})
    or flat structures.
    """
    # Flatten nested structures: if top-level keys don't include expected fields,
    # look one level deeper.
    expected_keys = {"guidance_text", "safety_notes", "confidence_notes"}
    if not expected_keys.intersection(payload.keys()):
        for value in payload.values():
            if isinstance(value, dict) and expected_keys.intersection(value.keys()):
                payload = {**payload, **value}
                break

    def _clean(value: Any, fallback: str) -> str:
        if isinstance(value, str):
            clean_value = value.strip()
            if clean_value:
                return clean_value
        if isinstance(value, dict) or isinstance(value, list):
            # Flatten nested dict/list into a string representation.
            return json.dumps(value, ensure_ascii=False)
        return fallback

    guidance_text = _clean(
        payload.get("guidance_text"),
        "",
    )
    safety_notes = _clean(
        payload.get("safety_notes"),
        "",
    )
    confidence_notes = _clean(
        payload.get("confidence_notes"),
        "",
    )

    # Generate fallback text if key fields are empty.
    if not guidance_text:
        guidance_text = "I could not confidently interpret the scene. Pause, use your cane to sweep the area, and proceed slowly toward the clearest path."
    if not safety_notes:
        safety_notes = "Stay cautious, move slowly, and verify surroundings before each step."
    if not confidence_notes:
        confidence_notes = "Low confidence due to limited scene details."

    # Derive a risk score if present.
    risk_score = 35
    if isinstance(payload.get("risk_score"), (int, float)):
        risk_score = max(0, min(int(payload["risk_score"]), 100))

    return GuidanceResponse(
        guidance_text=guidance_text,
        safety_notes=safety_notes,
        confidence_notes=confidence_notes,
        mode="qwen",
        risk_score=risk_score,
    )


def validate_guidance_quality(response: GuidanceResponse) -> dict[str, Any]:
    """Check response quality and return a quality report.

    Returns a dict with 'valid' (bool), 'issues' (list of str), and 'quality' (low/medium/high).
    """
    issues: list[str] = []

    if len(response.guidance_text) < MIN_GUIDANCE_LENGTH:
        issues.append("guidance_text is very short, may lack actionable detail")
    if len(response.safety_notes) < MIN_SAFETY_LENGTH:
        issues.append("safety_notes is very short, may lack specific warnings")
    if response.confidence_notes and "low confidence" in response.confidence_notes.lower():
        issues.append("model reports low confidence")

    # Check for placeholder-like content.
    for field_name in ("guidance_text", "safety_notes", "confidence_notes"):
        val = getattr(response, field_name, "")
        if val and ("placeholder" in val.lower() or "todo" in val.lower()):
            issues.append(f"{field_name} appears to contain placeholder text")

    quality = "high"
    if len(issues) >= 2:
        quality = "low"
    elif len(issues) == 1:
        quality = "medium"

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "quality": quality,
    }
