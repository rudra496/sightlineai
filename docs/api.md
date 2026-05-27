# API Reference

> Complete reference for the SightlineAI REST API (v0.2.0)

**Table of Contents**
- [Authentication](#authentication)
- [Error Responses](#error-responses)
- [GET /api/health](#get-apihealth)
- [POST /api/guidance](#post-apiguidance)
- [POST /api/fallback-guidance](#post-apifallback-guidance)
- [POST /api/analyze-image](#post-apianalyze-image)
- [POST /api/edge-context](#post-apiedge-context)
- [GET /api/session-history](#get-apisession-history)
- [POST /api/session-history](#post-apisession-history)
- [DELETE /api/session-history](#delete-apisession-history)
- [Rate Limiting](#rate-limiting)

---

## Authentication

No authentication is required for local development. The API key (`DASHSCOPE_API_KEY`) is a server-side environment variable used only for Qwen AI calls — it is never passed by clients.

## Error Responses

All errors follow a consistent JSON schema:

```json
{
  "error": "error_code",
  "detail": "Human-readable message",
  "request_id": "uuid-for-tracing"
}
```

| HTTP Status | Error Code | Meaning |
|---|---|---|
| 400 | `invalid_input` | Request body failed Pydantic validation |
| 400 | `invalid_image` | Image upload failed type/size validation |
| 413 | `payload_too_large` | Request body exceeds 10 MB |
| 429 | `rate_limited` | Too many requests (60/min per IP) |
| 500 | `http_error` | Internal server error |

**Example validation error:**
```json
{
  "error": "invalid_input",
  "detail": "Request body failed validation. Check required fields and data types.",
  "request_id": "a1b2c3d4-...",
  "validation": [
    {
      "loc": ["body", "scene_description"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

---

## GET /api/health

Returns service health and configuration status.

**curl:**
```bash
curl http://localhost:8000/api/health
```

**Response (200):**
```json
{
  "status": "ok",
  "service": "SightlineAI",
  "version": "0.2.0",
  "python_version": "3.11.9",
  "uptime_seconds": 142.3,
  "model": "qwen3.7-max",
  "api_key_configured": true,
  "fallback_enabled": true,
  "timestamp": "2025-05-27T08:30:00+00:00"
}
```

---

## POST /api/guidance

Generate environmental guidance with automatic Qwen → fallback degradation.

**curl:**
```bash
curl -X POST http://localhost:8000/api/guidance \
  -H "Content-Type: application/json" \
  -d '{
    "scene_description": "I am at an intersection with barriers ahead and traffic sounds",
    "geospatial_context": {
      "location_label": "Main Street crossing",
      "route_description": "Heading eastbound",
      "time_of_day": "dusk",
      "known_hazards": ["construction", "uneven_pavement"],
      "mobility_aid": "white_cane"
    }
  }'
```

**Request Body (`GuidanceRequest`):**

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `scene_description` | string | ✅ | 5–2000 chars | Textual description of the environment |
| `geospatial_context` | object | ❌ | — | Optional location/route context |

**Geospatial Context Fields:**

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `location_label` | string | ❌ | max 120 chars | Named location |
| `route_description` | string | ❌ | max 280 chars | Route being followed |
| `time_of_day` | string | ❌ | `day`, `night`, `dawn`, `dusk` | Ambient light context |
| `known_hazards` | string[] | ❌ | max 8 items | Hazard tags for conservative scoring |
| `mobility_aid` | string | ❌ | max 80 chars | Mobility aid type |

**Response (200 — `GuidanceResponse`):**
```json
{
  "guidance_text": "Proceed cautiously. There is construction ahead with barriers blocking the eastbound lane. Stay to the right side of the sidewalk and listen for traffic from the north.",
  "safety_notes": "Dusk conditions reduce visibility for drivers. Construction barriers may have protruding elements. Uneven pavement reported in this area.",
  "confidence_notes": "Guidance is based on user-reported scene context and heuristic analysis. Not a substitute for certified navigation assistance.",
  "mode": "qwen",
  "fallback_reason": null,
  "risk_score": 62
}
```

**Fallback Response (mode: "fallback"):**
```json
{
  "guidance_text": "Exercise caution. Environmental context suggests potential hazards. Stay alert and use mobility aids if available.",
  "safety_notes": "Unable to generate AI-specific guidance. Defaulting to conservative safety recommendations.",
  "confidence_notes": "This is offline fallback guidance with limited environmental specificity.",
  "mode": "fallback",
  "fallback_reason": "missing_api_key",
  "risk_score": 45
}
```

Possible `fallback_reason` values: `"missing_api_key"`, `"upstream_unavailable"`, `"qwen_parse_error"`

---

## POST /api/fallback-guidance

Forces deterministic fallback guidance (no Qwen call). Ideal for demos and offline testing.

**curl:**
```bash
curl -X POST http://localhost:8000/api/fallback-guidance \
  -H "Content-Type: application/json" \
  -d '{
    "scene_description": "I hear water flowing nearby and the ground is muddy",
    "reason": "demo_mode"
  }'
```

**Request Body (`FallbackGuidanceRequest`):**

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `scene_description` | string | ✅ | 5–2000 chars | Scene description |
| `geospatial_context` | object | ❌ | — | Optional geospatial context (same as above) |
| `reason` | string | ❌ | max 120 chars | Reason for forcing fallback |

**Response:** Same `GuidanceResponse` schema with `"mode": "fallback"`.

---

## POST /api/analyze-image

Upload an image for accessibility-focused analysis. Uses `multipart/form-data`.

**curl:**
```bash
curl -X POST http://localhost:8000/api/analyze-image \
  -F "image=@photo.jpg" \
  -F "text_hint=Crossing a busy street" \
  -F "location_label=Station Road"
```

**Form Fields:**

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `image` | file | ✅ | PNG/JPEG/WEBP, max 5 MB | Image to analyze |
| `text_hint` | string | ❌ | max 200 chars | Additional context hint |
| `location_label` | string | ❌ | max 120 chars | Named location |
| `route_description` | string | ❌ | max 280 chars | Route being followed |

**Response (200 — `ImageAnalysisResponse`):**
```json
{
  "guidance_text": "The image suggests an outdoor urban environment. Proceed with caution and maintain awareness of surrounding traffic.",
  "safety_notes": "Image-based analysis provides general guidance only. Verify surroundings through other senses.",
  "confidence_notes": "Analysis is based on validated image metadata. Full OCR not yet enabled.",
  "mode": "fallback",
  "fallback_reason": null,
  "risk_score": 40,
  "image_summary": "Image received: JPEG format, processed with context hints.",
  "extracted_text": null
}
```

**Error Response (400):**
```json
{
  "error": "invalid_image",
  "detail": "Unsupported image format. Allowed: JPEG, PNG, WEBP.",
  "request_id": "e5f6g7h8-..."
}
```

---

## POST /api/edge-context

Submit sensor-like data for risk scoring. Designed for future hardware adapter integration.

**curl:**
```bash
curl -X POST http://localhost:8000/api/edge-context \
  -H "Content-Type: application/json" \
  -d '{
    "obstacle_distance_m": 1.5,
    "ambient_noise_db": 75.0,
    "motion_state": "walking",
    "gps_accuracy_m": 12.0,
    "battery_level": 45.0
  }'
```

**Request Body (`EdgeContextRequest`):**

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `obstacle_distance_m` | float | ❌ | 0–20 | Nearest obstacle distance |
| `ambient_noise_db` | float | ❌ | 0–140 | Ambient noise level |
| `motion_state` | string | ❌ | `still`, `walking`, `running`, `vehicle` | Current motion state |
| `gps_accuracy_m` | float | ❌ | 0–200 | GPS accuracy in meters |
| `battery_level` | float | ❌ | 0–100 | Device battery percentage |

**Response (200 — `EdgeContextResponse`):**
```json
{
  "risk_score": 58,
  "risk_band": "medium",
  "suggested_actions": [
    "Reduce walking speed — obstacle detected within 2 meters.",
    "Moderate ambient noise may mask audio cues. Increase alertness.",
    "GPS accuracy is moderate. Do not rely solely on positional data."
  ],
  "edge_ready": true
}
```

`risk_band` values: `"low"` (0–33), `"medium"` (34–66), `"high"` (67–100)

---

## GET /api/session-history

Retrieve all stored session history entries.

**curl:**
```bash
curl http://localhost:8000/api/session-history
```

**Response (200 — `SessionHistoryResponse`):**
```json
{
  "items": [
    {
      "id": "uuid-1",
      "created_at": "2025-05-27T08:15:00+00:00",
      "source": "guidance",
      "scene_description": "At an intersection with barriers",
      "guidance": {
        "guidance_text": "...",
        "safety_notes": "...",
        "confidence_notes": "...",
        "mode": "qwen",
        "fallback_reason": null,
        "risk_score": 62
      },
      "pinned": false
    }
  ]
}
```

`source` values: `"guidance"`, `"fallback"`, `"image"`, `"manual"`

---

## POST /api/session-history

Create a manual session history entry.

**curl:**
```bash
curl -X POST http://localhost:8000/api/session-history \
  -H "Content-Type: application/json" \
  -d '{
    "source": "manual",
    "scene_description": "At the bus stop on Elm Street",
    "guidance": {
      "guidance_text": "Wait at the current location.",
      "safety_notes": "Stay behind the curb line.",
      "confidence_notes": "Manual entry.",
      "mode": "fallback",
      "risk_score": 20
    },
    "pinned": true
  }'
```

**Response (200 — `SessionHistoryItem`):** Returns the created item with generated `id` and `created_at`.

---

## DELETE /api/session-history

Clear all session history entries.

**curl:**
```bash
curl -X DELETE http://localhost:8000/api/session-history
```

**Response (200):**
```json
{
  "cleared": true
}
```

---

## Rate Limiting

The API enforces a rate limit of **60 requests per minute per IP address**. Exceeding this limit returns:

```json
{
  "error": "rate_limited",
  "detail": "Too many requests. Try again later.",
  "request_id": "..."
}
```

With HTTP status `429` and a `Retry-After` header indicating the cooldown window.
