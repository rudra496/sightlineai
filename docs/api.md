# API Reference

## GET /api/health
Returns service status.

## POST /api/guidance
Generate guidance with automatic fallback.

Request:
```json
{
  "scene_description": "I am at an intersection with barriers ahead",
  "geospatial_context": {
    "location_label": "Main street",
    "route_description": "Crossing eastbound",
    "known_hazards": ["construction"]
  }
}
```

Response:
```json
{
  "guidance_text": "...",
  "safety_notes": "...",
  "confidence_notes": "...",
  "mode": "qwen",
  "fallback_reason": null,
  "risk_score": 62
}
```

## POST /api/fallback-guidance
Forces deterministic fallback guidance.

## POST /api/analyze-image
Multipart form fields:
- `image` (required)
- `text_hint` (optional)
- `location_label` (optional)
- `route_description` (optional)

Returns `ImageAnalysisResponse` with `image_summary` and structured guidance.

## POST /api/edge-context
Request body fields:
- `obstacle_distance_m`
- `ambient_noise_db`
- `motion_state`
- `gps_accuracy_m`
- `battery_level`

Returns risk score, band, and suggested actions.

## Session history
- `GET /api/session-history`
- `POST /api/session-history`
- `DELETE /api/session-history`

## Error schema
```json
{
  "error": "invalid_input",
  "detail": "Request body failed validation.",
  "request_id": "..."
}
```
