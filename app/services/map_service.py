from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger("sightlineai.map")

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
OSRM_BASE = "https://router.project-osrm.org"
OVERPASS_BASE = "https://overpass-api.depi"

DEFAULT_HEADERS = {"User-Agent": "SightlineAI/1.0 (assistive-navigation)"}


def search_location(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Geocode a location query using Nominatim API."""
    try:
        resp = requests.get(
            f"{NOMINATIM_BASE}/search",
            params={"q": query, "format": "json", "limit": limit, "addressdetails": 1},
            headers=DEFAULT_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        results = []
        for item in resp.json():
            results.append({
                "display_name": item.get("display_name", ""),
                "lat": float(item.get("lat", 0)),
                "lon": float(item.get("lon", 0)),
                "type": item.get("type", ""),
                "address": item.get("address", {}),
            })
        return results
    except Exception as exc:
        logger.error("Nominatim search failed: %s", exc)
        return []


def get_route(origin: tuple[float, float], destination: tuple[float, float]) -> dict[str, Any]:
    """Get walking route via OSRM."""
    try:
        coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
        resp = requests.get(
            f"{OSRM_BASE}/route/v1/walking/{coords}",
            params={"overview": "full", "geometries": "geojson", "steps": "true"},
            headers=DEFAULT_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            return {"available": False, "error": "No route found"}

        route = data["routes"][0]
        steps = []
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                steps.append({
                    "instruction": step.get("maneuver", {}).get("modifier", ""),
                    "name": step.get("name", ""),
                    "distance": step.get("distance", 0),
                    "duration": step.get("duration", 0),
                    "type": step.get("maneuver", {}).get("type", ""),
                })

        accessibility_notes = []
        for step in steps:
            if step["type"] in ("turn", "rotary"):
                accessibility_notes.append(f"Turn at {step['name'] or 'unnamed road'} — verify surface quality")
            if step.get("distance", 0) > 500:
                accessibility_notes.append(f"Long stretch on {step['name'] or 'path'} ({step['distance']:.0f}m)")

        return {
            "available": True,
            "distance_m": route.get("distance", 0),
            "duration_s": route.get("duration", 0),
            "geometry": route.get("geometry", {}),
            "steps": steps,
            "accessibility_notes": accessibility_notes,
        }
    except Exception as exc:
        logger.error("OSRM routing failed: %s", exc)
        return {"available": False, "error": str(exc)}


def get_nearby_hazards(lat: float, lon: float, radius: int = 200) -> dict[str, Any]:
    """Query Overpass API for accessibility hazards near a point."""
    query = f"""
    [out:json][timeout:10];
    (
      node["highway"="steps"](around:{radius},{lat},{lon});
      node["barrier"](around:{radius},{lat},{lon});
      way["highway"="steps"](around:{radius},{lat},{lon});
      way["construction"](around:{radius},{lat},{lon});
      node["highway"="crossing"](around:{radius},{lat},{lon});
      way["footway"="crossing"](around:{radius},{lat},{lon});
    );
    out center;
    """
    try:
        resp = requests.post(
            f"{OVERPASS_BASE}/api/interpreter",
            data={"data": query},
            headers=DEFAULT_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        hazards = []
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            elat = element.get("lat") or element.get("center", {}).get("lat")
            elon = element.get("lon") or element.get("center", {}).get("lon")
            hazard_type = "unknown"
            if tags.get("highway") == "steps":
                hazard_type = "steps"
            elif tags.get("barrier"):
                hazard_type = "barrier"
            elif tags.get("construction"):
                hazard_type = "construction"
            elif tags.get("highway") == "crossing" or tags.get("footway") == "crossing":
                hazard_type = "crossing"

            hazards.append({
                "type": hazard_type,
                "lat": elat,
                "lon": elon,
                "tags": tags,
                "name": tags.get("name", ""),
            })

        return {"available": True, "count": len(hazards), "hazards": hazards}
    except Exception as exc:
        logger.error("Overpass query failed: %s", exc)
        return {"available": False, "error": str(exc), "count": 0, "hazards": []}


def get_accessibility_tiles(lat: float, lon: float, radius: int = 300) -> dict[str, Any]:
    """Return OSM accessibility features nearby."""
    query = f"""
    [out:json][timeout:10];
    (
      way["wheelchair"](around:{radius},{lat},{lon});
      node["wheelchair"](around:{radius},{lat},{lon});
      way["tactile_paving"](around:{radius},{lat},{lon});
      node["tactile_paving"](around:{radius},{lat},{lon});
      node["highway"="traffic_signals"](around:{radius},{lat},{lon});
      way["footway"](around:{radius},{lat},{lon});
      node["amenity"="toilets"]["wheelchair"](around:{radius},{lat},{lon});
    );
    out center;
    """
    try:
        resp = requests.post(
            f"{OVERPASS_BASE}/api/interpreter",
            data={"data": query},
            headers=DEFAULT_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        features = []
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            elat = element.get("lat") or element.get("center", {}).get("lat")
            elon = element.get("lon") or element.get("center", {}).get("lon")
            features.append({
                "type": tags.get("highway") or tags.get("amenity") or tags.get("footway") or "feature",
                "lat": elat,
                "lon": elon,
                "wheelchair": tags.get("wheelchair"),
                "tactile_paving": tags.get("tactile_paving"),
                "name": tags.get("name", ""),
                "tags": tags,
            })

        return {"available": True, "count": len(features), "features": features}
    except Exception as exc:
        logger.error("Overpass accessibility query failed: %s", exc)
        return {"available": False, "error": str(exc), "count": 0, "features": []}
