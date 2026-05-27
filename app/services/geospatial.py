from __future__ import annotations

from app.schemas import GeospatialContext

# Conservative adjustment for low-visibility periods (night/dawn/dusk).
TIME_OF_DAY_RISK_BONUS = 10
# Slight reduction because mobility aids can improve controlled movement.
MOBILITY_AID_RISK_REDUCTION = 5


def compute_geospatial_risk(context: GeospatialContext | None) -> int:
    """Return conservative risk score (0-100) from optional route context keywords."""
    if context is None:
        return 35

    score = 30
    route = (context.route_description or "").lower()
    location = (context.location_label or "").lower()
    hazards = [h.lower() for h in context.known_hazards]

    risk_keywords = {
        "construction": 20,
        "highway": 25,
        "intersection": 18,
        "stairs": 15,
        "crowded": 12,
        "night": 10,
        "rain": 8,
        "unlit": 12,
    }
    for keyword, points in risk_keywords.items():
        if keyword in route or keyword in location or any(keyword in h for h in hazards):
            score += points

    if context.time_of_day in {"night", "dawn", "dusk"}:
        score += TIME_OF_DAY_RISK_BONUS

    if context.mobility_aid:
        score -= MOBILITY_AID_RISK_REDUCTION

    return max(10, min(score, 100))


def risk_band(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"
