from __future__ import annotations

from app.schemas import GeospatialContext, GuidanceResponse
from app.services.geospatial import compute_geospatial_risk, risk_band


HAZARD_RULES = {
    "stairs": "There may be stairs nearby; use the handrail side if available and probe each step.",
    "traffic": "Traffic risk detected; pause and verify flow direction before crossing.",
    "vehicle": "Moving vehicle risk is possible; keep to a protected edge and listen for engine movement.",
    "wet": "Surface may be slippery; shorten stride and keep one hand free for stability.",
    "construction": "Construction hazards likely; expect temporary barriers and uneven ground.",
    "crowd": "Crowded conditions likely; keep a steady pace and maintain cane sweep width.",
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


def build_fallback_guidance(
    scene_description: str,
    geospatial_context: GeospatialContext | None = None,
    reason: str | None = None,
) -> GuidanceResponse:
    risk_score = compute_geospatial_risk(geospatial_context)
    hazards = _collect_hazards(scene_description, geospatial_context)

    route_note = ""
    if geospatial_context and geospatial_context.route_description:
        route_note = f" Follow route context: {geospatial_context.route_description.strip()}."

    guidance = (
        "Fallback guidance mode: pause, orient with your cane sweep, then move in short controlled steps "
        "toward the clearest path while keeping one side as a tactile reference."
        f"{route_note}"
    )

    safety = " ".join(hazards) if hazards else "No specific hazard keyword detected; continue cautiously and verify each step physically."
    confidence = (
        f"Deterministic offline estimate ({risk_band(risk_score)} risk, score {risk_score}/100). "
        "Confirm surroundings with cane/audio cues before committing to turns."
    )

    return GuidanceResponse(
        guidance_text=guidance.strip(),
        safety_notes=safety,
        confidence_notes=confidence,
        mode="fallback",
        fallback_reason=reason or "offline_fallback",
        risk_score=risk_score,
    )
