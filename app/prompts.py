from __future__ import annotations

import json

from app.schemas import GeospatialContext

SYSTEM_PROMPT = (
    "You are SightlineAI, an accessibility-first navigation assistant for blind and visually impaired users. "
    "Your guidance must be calm, practical, and safety-first.\n\n"
    "CORE PRINCIPLES:\n"
    "- Always prioritize safety over speed. Suggest stopping when uncertain.\n"
    "- Provide spatial directions using clock-face orientation (e.g. 'obstacle at 2 o'clock') "
    "and distance estimates when possible.\n"
    "- Identify hazards PROACTIVELY — mention potential risks even if not explicitly described.\n"
    "- Suggest verification steps: use cane sweeps, listen for audio cues, feel for tactile markers.\n"
    "- Handle uncertainty honestly. NEVER fabricate or guess details about the scene. "
    "If information is ambiguous, say so explicitly and recommend caution.\n"
    "- Use simple, direct language. Avoid jargon, idioms, or metaphorical descriptions.\n"
    "- Avoid markdown formatting. Use plain text only.\n\n"
    "OUTPUT FORMAT:\n"
    "You MUST respond with ONLY a valid JSON object with exactly these string keys: "
    '"guidance_text", "safety_notes", "confidence_notes". '
    "No additional keys, no wrapping, no explanation outside the JSON.\n\n"
    "FIELD GUIDELINES:\n"
    '- guidance_text: 1-3 action-oriented navigation steps. Include direction and distance hints.\n'
    '- safety_notes: 1-2 concrete hazard warnings with specific avoidance advice.\n'
    '- confidence_notes: 1 sentence stating confidence level and recommending a verification step.'
)

# Language instruction map for multi-language support.
RESPONSE_LANGUAGE_MAP: dict[str, str] = {
    "en": "",
    "bn": "You MUST respond in Bengali (Bangla). Write all guidance_text, safety_notes, and confidence_notes in Bengali script. Do not use English except for technical terms.",
    "ar": "You MUST respond in Arabic. Write all guidance_text, safety_notes, and confidence_notes in Arabic script. Use right-to-left appropriate language.",
    "es": "You MUST respond in Spanish. Write all guidance_text, safety_notes, and confidence_notes in Spanish.",
}


def get_system_prompt(language: str = "en") -> str:
    """Return system prompt with optional language instruction appended."""
    lang_instruction = RESPONSE_LANGUAGE_MAP.get(language, "")
    if lang_instruction:
        return SYSTEM_PROMPT + "\n\n" + lang_instruction
    return SYSTEM_PROMPT


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


def build_image_analysis_prompt(
    scene_description: str,
    filename: str | None = None,
    brightness_estimate: str | None = None,
    dimensions_hint: str | None = None,
    geospatial_context: GeospatialContext | None = None,
) -> str:
    """Build a prompt tailored for image analysis queries."""
    extra_context_parts = []
    if filename:
        extra_context_parts.append(f"Image filename: {filename}")
    if brightness_estimate:
        extra_context_parts.append(f"Brightness estimate: {brightness_estimate}")
    if dimensions_hint:
        extra_context_parts.append(f"Image dimensions hint: {dimensions_hint}")

    extra_context = ". ".join(extra_context_parts)
    if extra_context:
        extra_context = f" Additional metadata: {extra_context}."
    else:
        extra_context = ""

    payload = {
        "task": (
            "Analyze an uploaded image for accessibility guidance. "
            "Describe visible elements relevant to safe navigation. "
            "If the image is unclear or low quality, state that honestly rather than guessing details."
        ),
        "scene_description": scene_description,
        "image_context": extra_context.strip() or None,
        "geospatial_context": geospatial_context.model_dump() if geospatial_context else None,
        "response_format": {
            "guidance_text": "Navigation guidance based on image content (1-3 sentences).",
            "safety_notes": "Specific hazards visible or likely in the image (1-2 sentences).",
            "confidence_notes": "Confidence level given image quality and content (1 sentence).",
        },
    }
    return json.dumps(payload, ensure_ascii=False)


# --- Bangla fallback guidance templates ---
FALLBACK_TEMPLATES_BN: dict[str, str] = {
    "guidance_text": (
        "ফলব্যাক গাইডেন্স মোড: বিরতি নিন, আপনার ক্যান দিয়ে পরিবেশ পরীক্ষা করুন, "
        "তারপর স্পষ্টতম পথে ছোট নিয়ন্ত্রিত পদক্ষেপে এগিয়ে যান।"
    ),
    "safety_notes": "কোনো নির্দিষ্ট বিপদের কীওয়ার্ড শনাক্ত হয়নি; সতর্কতার সাথে এগিয়ে যান এবং প্রতিটি পদক্ষেপ শারীরিকভাবে যাচাই করুন।",
    "confidence_notes": "নির্ধারণবাদী অফলাইন অনুমান। মোড় নেওয়ার আগে ক্যান/অডিও সংকেত দিয়ে নিশ্চিত হন।",
}
