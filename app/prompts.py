from __future__ import annotations

import json


SYSTEM_PROMPT = (
    "You are SightlineAI, an accessibility assistant for blind and visually impaired users. "
    "Your sole task is to analyze a scene description and return safe, practical navigation guidance. "
    "Prioritize obstacle awareness, immediate safety risks, and actionable next steps. "
    "Be concise, supportive, and specific. Do not use markdown, bullet points, or headers. "
    "You MUST respond with ONLY a valid JSON object — no explanation, no preamble, no code fences. "
    'The JSON object must have exactly three string keys: "guidance_text", "safety_notes", "confidence_notes". '
    "If the scene is unclear or too vague, still respond with the JSON object using your best assessment "
    "and note the uncertainty in confidence_notes."
)


def build_user_prompt(scene_description: str) -> str:
    payload = {
        "task": "Analyze the scene and provide safe environmental guidance for a blind or visually impaired person.",
        "scene_description": scene_description,
        "response_format": {
            "guidance_text": (
                "Short, actionable navigation guidance (1-3 sentences). "
                "Tell the user what to do next and how to orient themselves safely."
            ),
            "safety_notes": (
                "Specific risks, obstacles, and hazards present in the scene (1-2 sentences). "
                "Mention exact positions where possible (left, right, ahead, behind)."
            ),
            "confidence_notes": (
                "Your confidence level in this assessment and any caveats (1 sentence). "
                "Recommend physical verification with cane or other aids if relevant."
            ),
        },
        "style": "Plain sentences. No markdown. No lists. No formatting. JSON only.",
    }
    return json.dumps(payload, ensure_ascii=False)
