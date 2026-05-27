from __future__ import annotations

from app.schemas import GeospatialContext, GuidanceResponse
from app.services.geospatial import compute_geospatial_risk, risk_band

# Bangla fallback templates
FALLBACK_TEMPLATES_BN = {
    "guidance_text": "ফলব্যাক গাইডেন্স মোড: বিরতি নিন, আপনার ক্যান দিয়ে পরিবেশ পরীক্ষা করুন।",
    "safety_notes": "সতর্কতার সাথে এগিয়ে যান।",
    "confidence_notes": "নির্ধারণবাদী অফলাইন অনুমান। ক্যান/অডিও সংকেত দিয়ে নিশ্চিত হন।",
}

# Safety-first neutral wording used when high-confidence inference is unavailable.
DEFAULT_FALLBACK_GUIDANCE_TEXT = (
    "Fallback guidance mode: pause, orient with your cane sweep, then move in short controlled "
    "steps toward the clearest path while keeping one side as a tactile reference."
)

HAZARD_RULES = {
    "stairs": "There may be stairs nearby; use the handrail side if available and probe each step.",
    "traffic": "Traffic risk detected; pause and verify flow direction before crossing.",
    "vehicle": "Moving vehicle risk is possible; keep to a protected edge and listen for engine movement.",
    "wet": "Surface may be slippery; shorten stride and keep one hand free for stability.",
    "construction": "Construction hazards likely; expect temporary barriers and uneven ground.",
    "crowd": "Crowded conditions likely; keep a steady pace and maintain cane sweep width.",
    # Extended hazard keyword rules.
    "elevator": "Elevator nearby; verify door alignment before entering, listen for arrival chime.",
    "escalator": "Escalator detected; use handrails, step on at the marked zone, and stand centered.",
    "puddle": "Possible puddle or standing water; probe ground ahead to avoid slipping.",
    "gravel": "Gravel or loose surface likely; move slowly, maintain balance, use cane to test footing.",
    "curb": "Curb or step-down may be present; probe ahead with cane to detect the edge.",
    "ramp": "Ramp detected; note the slope direction and maintain controlled pace.",
    "door": "Door ahead; check if it opens toward or away from you before approaching.",
    "gate": "Gate present; verify latch mechanism and clearance before passing through.",
    "bicycle": "Bicycle or bike path nearby; listen for approach and keep to the designated walking side.",
    "animal": "Animal may be present; remain still until it passes or you can determine a safe path around it.",
    "low ceiling": "Low ceiling or overhang ahead; raise your hand to check clearance.",
    "uneven": "Uneven surface likely; take short steps and test each foot placement.",
    "narrow": "Narrow passage ahead; proceed single-file and keep hands near your sides.",
    "dark": "Low-light conditions reported; rely more on audio cues and cane feedback.",
    "loud": "High noise level; audio cues may be masked, rely on tactile and cane feedback.",
}

# Seasonal/weather context adjustments.
SEASONAL_NOTES = {
    "winter": "Winter conditions: watch for ice, shortened stride recommended.",
    "summer": "Summer conditions: stay hydrated, watch for heat shimmer distorting visual cues.",
    "monsoon": "Monsoon conditions: expect sudden wet surfaces and reduced visibility.",
    "rain": "Rainy conditions: surfaces slippery, use extra caution on smooth floors.",
    "snow": "Snow conditions: footing unstable, use cane to probe depth.",
}

# Time-of-day specific guidance.
TIME_OF_DAY_NOTES = {
    "night": "Night conditions: rely heavily on audio and tactile cues. Use any available light source.",
    "dawn": "Dawn conditions: light changing rapidly, visibility may be inconsistent.",
    "dusk": "Dusk conditions: light fading, transition to audio/tactile reliance.",
}

# Mobility-aid specific tips.
MOBILITY_AID_TIPS = {
    "cane": "With cane: maintain consistent sweep pattern, two-point touch technique.",
    "white_cane": "With white cane: ensure sweep covers full body width, listen for echo changes.",
    "guide_dog": "With guide dog: trust the dog's path-finding, give clear directional commands.",
    "dog": "With guide dog: trust the dog's path-finding, give clear directional commands.",
    "wheelchair": "With wheelchair: check surface traction, watch for small steps or lips at thresholds.",
    "walker": "With walker: ensure stable placement before shifting weight, test surface ahead.",
    "prosthetic": "With prosthetic: extra caution on uneven surfaces, verify footing with cane if available.",
}


def _collect_hazards(scene: str, context: GeospatialContext | None) -> list[str]:
    text = scene.lower()
    found = [message for key, message in HAZARD_RULES.items() if key in text]
    if context:
        for hazard in context.known_hazards:
            lowered = hazard.lower()
            for key, message in HAZARD_RULES.items():
                if key in lowered and message not in found:
                    found.append(message)
    return found


def _get_seasonal_notes(scene: str) -> str:
    """Return seasonal/weather context guidance based on scene text."""
    text = scene.lower()
    notes = [note for key, note in SEASONAL_NOTES.items() if key in text]
    return " ".join(notes)


def _get_time_of_day_notes(context: GeospatialContext | None) -> str:
    """Return time-of-day specific guidance."""
    if not context or not context.time_of_day:
        return ""
    return TIME_OF_DAY_NOTES.get(context.time_of_day, "")


def _get_mobility_aid_notes(context: GeospatialContext | None) -> str:
    """Return mobility-aid specific tips."""
    if not context or not context.mobility_aid:
        return ""
    aid_lower = context.mobility_aid.lower()
    for key, tip in MOBILITY_AID_TIPS.items():
        if key in aid_lower:
            return tip
    return ""


def _build_multi_step_guidance(hazards: list[str], scene: str, context: GeospatialContext | None) -> str:
    """Build multi-step guidance for complex scenes with multiple hazards."""
    if len(hazards) <= 2:
        return ""

    steps = ["Multiple hazards detected — follow these steps:"]
    for i, hazard in enumerate(hazards[:4], 1):
        steps.append(f"  {i}. {hazard}")
    steps.append("  Proceed only after addressing each identified hazard.")
    return " ".join(steps)


def build_fallback_guidance(
    scene_description: str,
    geospatial_context: GeospatialContext | None = None,
    reason: str | None = None,
    language: str = "en",
) -> GuidanceResponse:
    risk_score = compute_geospatial_risk(geospatial_context)
    hazards = _collect_hazards(scene_description, geospatial_context)

    # Build route context note.
    route_note = ""
    if geospatial_context and geospatial_context.route_description:
        route_note = f" Follow route context: {geospatial_context.route_description.strip()}."

    # Build guidance text with contextual additions.
    guidance_parts = [DEFAULT_FALLBACK_GUIDANCE_TEXT]

    seasonal = _get_seasonal_notes(scene_description)
    if seasonal:
        guidance_parts.append(seasonal)

    time_note = _get_time_of_day_notes(geospatial_context)
    if time_note:
        guidance_parts.append(time_note)

    aid_note = _get_mobility_aid_notes(geospatial_context)
    if aid_note:
        guidance_parts.append(aid_note)

    guidance_parts.append(route_note.strip())
    guidance = " ".join(part for part in guidance_parts if part).strip()

    # Safety notes with multi-step guidance for complex scenes.
    safety_parts = []
    multi_step = _build_multi_step_guidance(hazards, scene_description, geospatial_context)
    if multi_step:
        safety_parts.append(multi_step)

    if hazards:
        safety_parts.append(" ".join(hazards))
    else:
        safety_parts.append("No specific hazard keyword detected; continue cautiously and verify each step physically.")

    safety = " ".join(safety_parts)

    confidence = (
        f"Deterministic offline estimate ({risk_band(risk_score)} risk, score {risk_score}/100). "
        "Confirm surroundings with cane/audio cues before committing to turns."
    )

    if language == "bn":
        guidance = FALLBACK_TEMPLATES_BN.get("guidance_text", guidance)
        safety = FALLBACK_TEMPLATES_BN.get("safety_notes", safety)
        confidence = FALLBACK_TEMPLATES_BN.get("confidence_notes", confidence)

    return GuidanceResponse(
        guidance_text=guidance,
        safety_notes=safety,
        confidence_notes=confidence,
        mode="fallback",
        fallback_reason=reason or "offline_fallback",
        risk_score=risk_score,
    )
