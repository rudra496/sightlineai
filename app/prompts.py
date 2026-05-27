from __future__ import annotations

import json

from app.schemas import GeospatialContext


SYSTEM_PROMPT = (
    "You are SightlineAI, an accessibility assistant for blind and visually impaired users. "
    "Provide calm, practical, safety-first guidance. Avoid speculative claims and avoid markdown. "
    "You MUST respond with ONLY a valid JSON object with exactly these string keys: "
    '"guidance_text", "safety_notes", "confidence_notes". '
    "Keep guidance concise and action-oriented."
)


def build_user_prompt(scene_description: str, geospatial_context: GeospatialContext | None = None) -> str:
    payload = {
        "task": "Analyze the scene and provide safe navigation guidance.",
        "scene_description": scene_description,
        "geospatial_context": geospatial_context.model_dump() if geospatial_context else None,
        "response_format": {
            "guidance_text": "Action-oriented navigation steps (1-3 sentences).",
            "safety_notes": "Concrete hazard and obstacle warnings (1-2 sentences).",
            "confidence_notes": "Confidence and verification caveat (1 sentence).",
        },
    }
    return json.dumps(payload, ensure_ascii=False)
