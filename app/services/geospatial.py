from __future__ import annotations

from app.schemas import GeospatialContext

# Conservative adjustment for low-visibility periods (night/dawn/dusk).
TIME_OF_DAY_RISK_BONUS = 10

# Weather condition risk modifiers.
WEATHER_RISK_SCORES = {
    "rain": 12,
    "snow": 15,
    "ice": 20,
    "fog": 10,
    "storm": 18,
    "wind": 8,
    "hail": 20,
}

# Mobility aid adjustments — different aids provide different risk reduction.
MOBILITY_AID_ADJUSTMENTS = {
    "cane": -5,
    "white_cane": -5,
    "guide_dog": -8,
    "dog": -8,
    "wheelchair": -3,
    "walker": -4,
    "prosthetic": -2,
}


def compute_geospatial_risk(context: GeospatialContext | None) -> int:
    """Return conservative risk score (0-100) from optional route context keywords."""
    if context is None:
        return 35

    score = 30
    route = (context.route_description or "").lower()
    location = (context.location_label or "").lower()
    hazards = [h.lower() for h in context.known_hazards]
    all_text = f"{route} {location} " + " ".join(hazards)

    risk_keywords = {
        "construction": 20,
        "highway": 25,
        "intersection": 18,
        "stairs": 15,
        "crowded": 12,
        "night": 10,
        "rain": 8,
        "unlit": 12,
        # New risk keywords
        "bridge": 14,
        "tunnel": 16,
        "parking": 12,
        "railway": 22,
        "train": 22,
        "school": 10,
        "hospital": 8,
        "market": 12,
        "bazaar": 12,
        "mall": 10,
        "crossing": 15,
        "roundabout": 14,
        "overpass": 12,
        "underpass": 14,
    }
    for keyword, points in risk_keywords.items():
        if keyword in all_text:
            score += points

    # Time of day risk.
    if context.time_of_day in {"night", "dawn", "dusk"}:
        score += TIME_OF_DAY_RISK_BONUS

    # Weather context scoring.
    for condition, points in WEATHER_RISK_SCORES.items():
        if condition in all_text:
            score += points

    # Mobility aid adjustment.
    if context.mobility_aid:
        aid_lower = context.mobility_aid.lower()
        aid_matched = False
        for aid_key, adjustment in MOBILITY_AID_ADJUSTMENTS.items():
            if aid_key in aid_lower:
                score += adjustment
                aid_matched = True
                break
        if not aid_matched:
            # Generic aid provides a small reduction.
            score -= 3

    # Route complexity scoring — longer descriptions with multiple segments increase risk.
    route_text = (context.route_description or "").strip()
    if route_text:
        turns = sum(1 for word in ["turn", "left", "right", "curve", "bend", "u-turn", "fork"] if word in route_text.lower())
        score += min(turns * 3, 12)

    return max(10, min(score, 100))


def risk_band(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"
