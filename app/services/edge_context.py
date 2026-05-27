from __future__ import annotations

from app.schemas import EdgeContextRequest, EdgeContextResponse
from app.services.geospatial import risk_band

# Above this level, environmental audio cues become less reliable for navigation.
NOISE_RISK_THRESHOLD_DB = 75

# Battery level thresholds for warnings.
BATTERY_WARNING_THRESHOLD = 20
BATTERY_CRITICAL_THRESHOLD = 10

# GPS accuracy thresholds.
GPS_DEGRADED_THRESHOLD_M = 25
GPS_POOR_THRESHOLD_M = 50


def evaluate_edge_context(payload: EdgeContextRequest) -> EdgeContextResponse:
    score = 25

    # --- Obstacle proximity scoring (nuanced tiers) ---
    if payload.obstacle_distance_m is not None:
        if payload.obstacle_distance_m < 0.5:
            score += 55  # Very close — immediate collision risk
        elif payload.obstacle_distance_m < 1.0:
            score += 40
        elif payload.obstacle_distance_m < 2.0:
            score += 25
        elif payload.obstacle_distance_m < 3.0:
            score += 10  # Moderate distance
        elif payload.obstacle_distance_m < 5.0:
            score += 5   # Distant but notable

    # --- Ambient noise scoring ---
    if payload.ambient_noise_db is not None and payload.ambient_noise_db > NOISE_RISK_THRESHOLD_DB:
        noise_overage = payload.ambient_noise_db - NOISE_RISK_THRESHOLD_DB
        score += min(15 + int(noise_overage / 5), 25)

    # --- Motion state scoring ---
    if payload.motion_state == "running":
        score += 30  # Running = less reaction time, more urgent
    elif payload.motion_state == "vehicle":
        score += 20
    elif payload.motion_state == "walking":
        score += 5   # Walking is baseline movement

    # --- GPS accuracy degradation warnings ---
    if payload.gps_accuracy_m is not None:
        if payload.gps_accuracy_m > GPS_POOR_THRESHOLD_M:
            score += 15
        elif payload.gps_accuracy_m > GPS_DEGRADED_THRESHOLD_M:
            score += 8

    # --- Battery level warnings ---
    if payload.battery_level is not None:
        if payload.battery_level < BATTERY_CRITICAL_THRESHOLD:
            score += 12
        elif payload.battery_level < BATTERY_WARNING_THRESHOLD:
            score += 6

    score = max(5, min(score, 100))

    # --- Build suggested actions ---
    actions = ["Keep cane sweep active and move in short steps."]

    if score >= 70:
        actions.append("Pause movement and re-evaluate obstacle distance before continuing.")
    if score >= 90:
        actions.append("HIGH RISK: Stop immediately. Find a safe resting point and reassess.")

    if payload.ambient_noise_db and payload.ambient_noise_db > NOISE_RISK_THRESHOLD_DB:
        actions.append("Use vibration/haptic cues because audio cues may be masked by noise.")

    # Motion state-specific guidance.
    if payload.motion_state == "running":
        actions.append("Running increases risk significantly. Slow to a walk and re-scan the environment.")
    elif payload.motion_state == "vehicle":
        actions.append("In a vehicle: ensure seatbelt is fastened and alert the driver to any concerns.")

    # Battery level warnings.
    if payload.battery_level is not None and payload.battery_level < BATTERY_CRITICAL_THRESHOLD:
        actions.append(
            f"Battery critically low ({payload.battery_level:.0f}%). "
            "Seek a charging point soon — assistive features may shut down."
        )
    elif payload.battery_level is not None and payload.battery_level < BATTERY_WARNING_THRESHOLD:
        actions.append(
            f"Battery low ({payload.battery_level:.0f}%). "
            "Consider finding a charging point in the next few minutes."
        )

    # GPS accuracy degradation warnings.
    if payload.gps_accuracy_m is not None and payload.gps_accuracy_m > GPS_POOR_THRESHOLD_M:
        actions.append(
            f"GPS accuracy very poor ({payload.gps_accuracy_m:.0f}m). "
            "Do not rely on GPS for navigation; use local cues."
        )
    elif payload.gps_accuracy_m is not None and payload.gps_accuracy_m > GPS_DEGRADED_THRESHOLD_M:
        actions.append(
            f"GPS accuracy degraded ({payload.gps_accuracy_m:.0f}m). "
            "Cross-reference with physical landmarks."
        )

    return EdgeContextResponse(
        risk_score=score,
        risk_band=risk_band(score),
        suggested_actions=actions,
        edge_ready=True,
    )
