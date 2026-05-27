from __future__ import annotations

import json


SYSTEM_PROMPT = (
    "You are SightlineAI, an accessibility assistant for blind and visually impaired users. "
    "Provide concise, practical, safety-aware guidance from scene descriptions. "
    "Prioritize obstacle awareness, navigation safety, and immediate next actions. "
    "Respond only as strict JSON with keys: guidance_text, safety_notes, confidence_notes."
)



def build_user_prompt(scene_description: str) -> str:
    payload = {
        "task": "Analyze the scene and provide safe environmental guidance.",
        "audience": "blind and visually impaired user",
        "scene_description": scene_description,
        "response_format": {
            "guidance_text": "short actionable navigation guidance",
            "safety_notes": "specific risks and obstacles",
            "confidence_notes": "confidence, uncertainty, and recommendation to verify"
        },
        "style": "concise, supportive, practical, no markdown"
    }
    return json.dumps(payload, ensure_ascii=False)
