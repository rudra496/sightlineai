from __future__ import annotations

from app.schemas import EdgeContextRequest, EdgeContextResponse
from app.services.geospatial import risk_band


def evaluate_edge_context(payload: EdgeContextRequest) -> EdgeContextResponse:
    score = 25

    if payload.obstacle_distance_m is not None:
        if payload.obstacle_distance_m < 1.0:
            score += 45
        elif payload.obstacle_distance_m < 2.0:
            score += 25

    if payload.ambient_noise_db is not None and payload.ambient_noise_db > 75:
        score += 15

    if payload.motion_state in {"running", "vehicle"}:
        score += 20

    if payload.gps_accuracy_m is not None and payload.gps_accuracy_m > 25:
        score += 8

    if payload.battery_level is not None and payload.battery_level < 15:
        score += 5

    score = max(5, min(score, 100))

    actions = ["Keep cane sweep active and move in short steps."]
    if score >= 70:
        actions.append("Pause movement and re-evaluate obstacle distance before continuing.")
    if payload.ambient_noise_db and payload.ambient_noise_db > 75:
        actions.append("Use vibration/haptic cues because audio cues may be masked by noise.")

    return EdgeContextResponse(
        risk_score=score,
        risk_band=risk_band(score),
        suggested_actions=actions,
        edge_ready=True,
    )
