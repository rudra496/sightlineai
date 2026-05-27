from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger("sightlineai.sensor")


class SensorReading:
    """Represents a single sensor reading."""

    def __init__(self, sensor_type: str, data: dict[str, Any], timestamp: str | None = None):
        self.sensor_type = sensor_type
        self.data = data
        self.timestamp = timestamp

    def to_dict(self) -> dict[str, Any]:
        return {"sensor_type": self.sensor_type, "data": self.data, "timestamp": self.timestamp}


class SensorAdapter:
    """Processes raw sensor data from various hardware sensors."""

    def process_lidar(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process LiDAR point cloud data."""
        points = data.get("points", [])
        distances = data.get("distances", [])

        if not distances and points:
            distances = [p.get("distance", 0) for p in points]

        if not distances:
            return {"processed": False, "error": "No distance data"}

        min_dist = min(distances)
        max_dist = max(distances)
        avg_dist = sum(distances) / len(distances)

        obstacles = [d for d in distances if d < 2.0]
        risk_level = "low"
        if min_dist < 0.5:
            risk_level = "critical"
        elif min_dist < 1.0:
            risk_level = "high"
        elif min_dist < 2.0:
            risk_level = "medium"

        return {
            "processed": True,
            "point_count": len(distances),
            "min_distance_m": round(min_dist, 3),
            "max_distance_m": round(max_dist, 3),
            "avg_distance_m": round(avg_dist, 3),
            "obstacle_count": len(obstacles),
            "risk_level": risk_level,
            "sensor_type": "lidar",
        }

    def process_imu(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process IMU (accelerometer + gyroscope) data."""
        accel = data.get("acceleration", {})
        gyro = data.get("gyroscope", {})
        mag = data.get("magnetometer", {})

        accel_x = accel.get("x", 0)
        accel_y = accel.get("y", 0)
        accel_z = accel.get("z", 0)
        accel_magnitude = math.sqrt(accel_x ** 2 + accel_y ** 2 + accel_z ** 2)

        gyro_x = gyro.get("x", 0)
        gyro_y = gyro.get("y", 0)
        gyro_z = gyro.get("z", 0)
        gyro_magnitude = math.sqrt(gyro_x ** 2 + gyro_y ** 2 + gyro_z ** 2)

        stability = "stable"
        if accel_magnitude > 15 or gyro_magnitude > 3:
            stability = "unstable"
        elif accel_magnitude > 12 or gyro_magnitude > 1.5:
            stability = "moderate"

        return {
            "processed": True,
            "acceleration_magnitude": round(accel_magnitude, 3),
            "gyroscope_magnitude": round(gyro_magnitude, 3),
            "has_magnetometer": bool(mag),
            "stability": stability,
            "tilt_detected": abs(accel_x) > 3.0 or abs(accel_y) > 3.0,
            "sensor_type": "imu",
        }

    def process_depth(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process depth camera data."""
        depth_map = data.get("depth_map", [])
        width = data.get("width", 0)
        height = data.get("height", 0)
        confidence = data.get("confidence", 1.0)

        if not depth_map:
            avg_depth = data.get("average_depth", 0)
            min_depth = data.get("min_depth", 0)
            if avg_depth:
                depth_map = [avg_depth] * 10
            else:
                return {"processed": False, "error": "No depth data"}

        avg_depth = sum(depth_map) / len(depth_map)
        min_depth = min(depth_map)
        max_depth = max(depth_map)

        drop_off = any(
            abs(depth_map[i] - depth_map[i + 1]) > 0.5
            for i in range(len(depth_map) - 1)
        )

        return {
            "processed": True,
            "avg_depth_m": round(avg_depth, 3),
            "min_depth_m": round(min_depth, 3),
            "max_depth_m": round(max_depth, 3),
            "resolution": f"{width}x{height}" if width and height else "unknown",
            "confidence": round(confidence, 2),
            "drop_off_detected": drop_off,
            "obstacle_in_path": min_depth < 1.5,
            "sensor_type": "depth",
        }

    def process_gps(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process GPS data."""
        lat = data.get("latitude")
        lon = data.get("longitude")
        accuracy = data.get("accuracy_m", 0)
        speed = data.get("speed_mps", 0)
        bearing = data.get("bearing", 0)

        if lat is None or lon is None:
            return {"processed": False, "error": "Missing latitude or longitude"}

        quality = "high"
        if accuracy > 20:
            quality = "low"
        elif accuracy > 10:
            quality = "medium"

        return {
            "processed": True,
            "latitude": lat,
            "longitude": lon,
            "accuracy_m": round(accuracy, 2),
            "speed_mps": round(speed, 2),
            "bearing": round(bearing, 1),
            "quality": quality,
            "sensor_type": "gps",
        }


def compute_sensor_fusion(readings: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine multiple sensor readings into a unified risk assessment."""
    if not readings:
        return {"risk_score": 0, "risk_level": "unknown", "factors": []}

    risk_score = 0
    factors = []
    sensor_types = set()

    for reading in readings:
        if not reading.get("processed"):
            continue
        stype = reading.get("sensor_type", "unknown")
        sensor_types.add(stype)

        if stype == "lidar":
            level = reading.get("risk_level", "low")
            if level == "critical":
                risk_score += 40
            elif level == "high":
                risk_score += 25
            elif level == "medium":
                risk_score += 15
            if reading.get("obstacle_count", 0) > 0:
                factors.append(f"LiDAR: {reading['obstacle_count']} obstacle(s) nearby")

        elif stype == "imu":
            stability = reading.get("stability", "stable")
            if stability == "unstable":
                risk_score += 30
            elif stability == "moderate":
                risk_score += 15
            if reading.get("tilt_detected"):
                risk_score += 10
                factors.append("IMU: Tilt detected")

        elif stype == "depth":
            if reading.get("obstacle_in_path"):
                risk_score += 25
                factors.append("Depth: Obstacle in path")
            if reading.get("drop_off_detected"):
                risk_score += 20
                factors.append("Depth: Drop-off detected")

        elif stype == "gps":
            quality = reading.get("quality", "high")
            if quality == "low":
                risk_score += 15
                factors.append("GPS: Low accuracy")
            elif quality == "medium":
                risk_score += 5

    risk_score = min(risk_score, 100)
    risk_level = "low"
    if risk_score >= 70:
        risk_level = "critical"
    elif risk_score >= 45:
        risk_level = "high"
    elif risk_score >= 25:
        risk_level = "medium"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "sensor_count": len(sensor_types),
        "sensor_types": list(sensor_types),
        "factors": factors,
    }


def generate_sensor_guidance(fusion_result: dict[str, Any]) -> dict[str, Any]:
    """Create guidance from sensor fusion data."""
    risk_level = fusion_result.get("risk_level", "low")
    factors = fusion_result.get("factors", [])
    guidance_parts = []
    safety_parts = []

    if risk_level == "critical":
        guidance_parts.append("STOP — Immediate hazard detected.")
        safety_parts.append("Do not proceed until the path is clear.")
    elif risk_level == "high":
        guidance_parts.append("CAUTION — Proceed very slowly with caution.")
        safety_parts.append("Use cane sweep and probe surroundings before each step.")
    elif risk_level == "medium":
        guidance_parts.append("Moderate risk detected — proceed with awareness.")
        safety_parts.append("Stay alert and maintain reduced speed.")
    else:
        guidance_parts.append("Path appears clear — continue with standard caution.")
        safety_parts.append("Maintain normal awareness.")

    if factors:
        guidance_parts.append("Detected: " + "; ".join(factors))

    return {
        "guidance_text": " ".join(guidance_parts),
        "safety_notes": " ".join(safety_parts),
        "risk_score": fusion_result.get("risk_score", 0),
        "risk_level": risk_level,
    }
