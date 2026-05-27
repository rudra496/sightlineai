from __future__ import annotations

import csv
import io
import logging
import os
import platform
import sys
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import (
    Depends, FastAPI, File, Form, HTTPException, Request, UploadFile,
    WebSocket, WebSocketDisconnect,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from app.config import get_settings, Settings
from app.qwen_client import MissingAPIKeyError, QwenClient, QwenClientError, UpstreamAPIError
from app.schemas import (
    AccessibilityScoreRequest,
    AccessibilityScoreResponse,
    AccessibilityTilesRequest,
    AccessibilityTilesResponse,
    AppSettings,
    ConversationRequest,
    ConversationResponse,
    EdgeContextRequest,
    EdgeContextResponse,
    ErrorResponse,
    FavoriteRequest,
    FallbackGuidanceRequest,
    GeospatialContext,
    GuidanceRequest,
    GuidanceResponse,
    HistorySearchRequest,
    ImageAnalysisResponse,
    LocationSearchRequest,
    LocationSearchResponse,
    NearbyHazardsRequest,
    NearbyHazardsResponse,
    OCRResponse,
    OfflineStatusResponse,
    PinRequest,
    RouteRequest,
    RouteResponse,
    SensorFusionRequest,
    SensorFusionResponse,
    SensorReadingRequest,
    SensorReadingResponse,
    SessionHistoryCreateRequest,
    SessionHistoryItem,
    SessionHistoryResponse,
    TokenResponse,
    UpdateSettingsRequest,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.edge_context import evaluate_edge_context
from app.services.fallback_guidance import build_fallback_guidance
from app.services.geospatial import compute_geospatial_risk
from app.services.history_store import SessionHistoryStore
from app.services.image_analysis import analyze_uploaded_image
from app.services.ocr_service import is_ocr_available as _is_ocr_available, extract_text_with_metadata
from app.services.map_service import search_location as _search_location, get_route as _get_route, get_nearby_hazards as _get_nearby_hazards, get_accessibility_tiles as _get_accessibility_tiles
from app.services.sensor_service import SensorAdapter, compute_sensor_fusion, generate_sensor_guidance
from app.services.auth_service import create_token, verify_token, invalidate_token, register_user as _register_user, authenticate_user as _authenticate_user, get_user as _get_user

# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("sightlineai")

# ---------------------------------------------------------------------------
# Settings & singletons
# ---------------------------------------------------------------------------
settings = get_settings()
qwen_client = QwenClient(settings)
history_store = SessionHistoryStore()
START_TIME = time.time()
IS_PRODUCTION = os.getenv("PRODUCTION", "false").lower() in ("true", "1", "yes")

# In-memory conversation store: session_id -> {messages, created_at, updated_at}
conversation_store: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# FastAPI app with lifespan for graceful shutdown
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Clean startup and shutdown."""
    logger.info("SightlineAI starting up (version %s)", settings.app_version)
    yield
    logger.info("SightlineAI shutting down – cleaning up resources…")
    qwen_client.close()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="SightlineAI API",
    version=settings.app_version,
    description="Accessibility-first guidance API with Qwen + offline fallback + image/edge context support.",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware: GZip compression → CORS → security
# ---------------------------------------------------------------------------
app.add_middleware(GZipMiddleware, minimum_size=500)

if IS_PRODUCTION:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ---------------------------------------------------------------------------
# Rate limiter (in-memory, 60 req/min per IP)
# ---------------------------------------------------------------------------
_rate_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 60
RATE_WINDOW = 60.0


def _rate_check(client_ip: str) -> bool:
    """Return True if the request is allowed."""
    now = time.time()
    timestamps = _rate_store.get(client_ip, [])
    timestamps = [t for t in timestamps if now - t < RATE_WINDOW]
    if len(timestamps) >= RATE_LIMIT:
        _rate_store[client_ip] = timestamps
        return False
    timestamps.append(now)
    _rate_store[client_ip] = timestamps
    return True


# ---------------------------------------------------------------------------
# Middleware: request ID, secure headers, rate limiting, request size
# ---------------------------------------------------------------------------
MAX_BODY_BYTES = 10 * 1024 * 1024  # 10 MB


@app.middleware("http")
async def security_middleware(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id

    client_ip = request.client.host if request.client else "unknown"
    if not _rate_check(client_ip):
        logger.warning("Rate limited %s on %s", client_ip, request.url.path)
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limited", "detail": "Too many requests. Try again later.", "request_id": request_id},
            headers={"Retry-After": str(int(RATE_WINDOW))},
        )

    if request.url.path != "/api/analyze-image":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"error": "payload_too_large", "detail": f"Request body exceeds {MAX_BODY_BYTES} bytes.", "request_id": request_id},
            )

    logger.info("[%s] %s %s", request_id, request.method, request.url.path)
    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    )
    return response


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------

def _error_payload(request: Request, error: str, detail: str) -> dict[str, str]:
    return {"error": error, "detail": detail, "request_id": getattr(request.state, "request_id", None)}


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            **_error_payload(request, "invalid_input", "Request body failed validation."),
            "validation": exc.errors(),
        },
    )


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail and "detail" in exc.detail:
        payload = dict(exc.detail)
        payload["request_id"] = getattr(request.state, "request_id", None)
        return JSONResponse(status_code=exc.status_code, content=payload)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(request, "http_error", str(exc.detail)),
    )


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "python_version": platform.python_version(),
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "model": settings.qwen_model,
        "api_key_configured": bool(settings.dashscope_api_key),
        "fallback_enabled": True,
        "circuit_breaker_open": qwen_client.circuit_open,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ocr_available": _is_ocr_available(),
    }


# ---------------------------------------------------------------------------
# Guidance endpoints
# ---------------------------------------------------------------------------

@app.post("/api/guidance", response_model=GuidanceResponse)
def guidance(request: GuidanceRequest) -> GuidanceResponse:
    try:
        fallback_reason: str | None = None
        response = qwen_client.get_guidance(
            request.scene_description, request.geospatial_context, language=request.language,
        )
        response.risk_score = compute_geospatial_risk(request.geospatial_context)
    except MissingAPIKeyError:
        fallback_reason = "missing_api_key"
    except UpstreamAPIError:
        fallback_reason = "upstream_unavailable"
    except QwenClientError:
        fallback_reason = "qwen_parse_error"

    if fallback_reason:
        response = build_fallback_guidance(
            scene_description=request.scene_description,
            geospatial_context=request.geospatial_context,
            reason=fallback_reason,
            language=request.language,
        )

    source = "fallback" if response.mode == "fallback" else "guidance"
    history_store.add_from_guidance(source=source, scene=request.scene_description, response=response)
    return response


@app.post("/api/fallback-guidance", response_model=GuidanceResponse)
def fallback_guidance(request: FallbackGuidanceRequest) -> GuidanceResponse:
    response = build_fallback_guidance(
        scene_description=request.scene_description,
        geospatial_context=request.geospatial_context,
        reason=request.reason or "manual_fallback",
        language=request.language,
    )
    history_store.add_from_guidance(source="fallback", scene=request.scene_description, response=response)
    return response


@app.post("/api/edge-context", response_model=EdgeContextResponse)
def edge_context(request: EdgeContextRequest) -> EdgeContextResponse:
    return evaluate_edge_context(request)


@app.post("/api/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(
    image: UploadFile = File(...),
    location_label: str | None = Form(default=None, max_length=120),
    route_description: str | None = Form(default=None, max_length=280),
    text_hint: str | None = Form(default=None, max_length=200),
    language: str = Form(default="en"),
) -> ImageAnalysisResponse:
    geospatial_context = GeospatialContext(
        location_label=location_label,
        route_description=route_description,
    )
    try:
        response = await analyze_uploaded_image(
            file=image,
            geospatial_context=geospatial_context,
            text_hint=text_hint,
            max_bytes=settings.image_max_bytes,
            language=language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "invalid_image", "detail": str(exc)}) from exc

    history_store.add_from_guidance(source="image", scene=text_hint or "Image upload", response=response)
    return response


# ---------------------------------------------------------------------------
# Session history CRUD
# ---------------------------------------------------------------------------

@app.get("/api/session-history", response_model=SessionHistoryResponse)
def get_session_history() -> SessionHistoryResponse:
    return SessionHistoryResponse(items=history_store.list_items())


@app.post("/api/session-history", response_model=SessionHistoryItem)
def create_session_history(request: SessionHistoryCreateRequest) -> SessionHistoryItem:
    item = SessionHistoryItem(
        id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        source=request.source,
        scene_description=request.scene_description,
        guidance=request.guidance,
        pinned=request.pinned,
    )
    return history_store.add_item(item)


@app.delete("/api/session-history/{item_id}")
def delete_session_history_item(item_id: str) -> dict[str, bool]:
    item = history_store.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": f"History item {item_id} not found"})
    history_store.delete(item_id)
    return {"deleted": True}


@app.delete("/api/session-history")
def clear_session_history() -> dict[str, bool]:
    history_store.clear()
    return {"cleared": True}


# ---------------------------------------------------------------------------
# Offline status
# ---------------------------------------------------------------------------

@app.get("/api/offline-status", response_model=OfflineStatusResponse)
def offline_status() -> OfflineStatusResponse:
    return OfflineStatusResponse(
        fallback_available=True,
        fallback_mode="deterministic",
        api_key_configured=bool(settings.dashscope_api_key),
        qwen_reachable=None,
        message="Deterministic fallback guidance is always available regardless of network state.",
    )


# ---------------------------------------------------------------------------
# History search, pin, export
# ---------------------------------------------------------------------------

@app.post("/api/session-history/search", response_model=SessionHistoryResponse)
def search_session_history(request: HistorySearchRequest) -> SessionHistoryResponse:
    items = history_store.search(
        source=request.source,
        keyword=request.keyword,
        date_from=request.date_from,
        date_to=request.date_to,
    )
    return SessionHistoryResponse(items=items)


@app.post("/api/session-history/pin")
def pin_history_item(request: PinRequest) -> dict:
    item = history_store.pin(request.item_id)
    if not item:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": f"Item {request.item_id} not found"})
    return {"pinned": True, "item_id": request.item_id}


@app.post("/api/session-history/unpin")
def unpin_history_item(request: PinRequest) -> dict:
    item = history_store.unpin(request.item_id)
    if not item:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": f"Item {request.item_id} not found"})
    return {"unpinned": True, "item_id": request.item_id}


@app.get("/api/session-history/export")
def export_session_history() -> dict:
    return {"items": history_store.export_all(), "count": len(history_store.list_items())}


@app.get("/api/session-history/export/csv")
def export_session_history_csv() -> Response:
    """Export session history as CSV."""
    items = history_store.list_items()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "created_at", "source", "scene_description", "guidance_text", "safety_notes", "confidence_notes", "risk_score", "mode", "pinned", "favorite"])
    for item in items:
        writer.writerow([
            item.id, item.created_at, item.source, item.scene_description,
            item.guidance.guidance_text, item.guidance.safety_notes,
            item.guidance.confidence_notes, item.guidance.risk_score,
            item.guidance.mode, item.pinned, item.favorite,
        ])
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=sightlineai_history.csv"})


@app.get("/api/session-history/export/markdown")
def export_session_history_markdown() -> Response:
    """Export session history as Markdown."""
    items = history_store.list_items()
    lines = ["# SightlineAI Session History\n"]
    for item in items:
        lines.append(f"## {item.created_at} ({item.source})")
        lines.append(f"**Scene:** {item.scene_description}\n")
        lines.append(f"**Guidance:** {item.guidance.guidance_text}")
        lines.append(f"**Safety:** {item.guidance.safety_notes}")
        lines.append(f"**Confidence:** {item.guidance.confidence_notes}")
        lines.append(f"**Risk:** {item.guidance.risk_score}/100 | **Mode:** {item.guidance.mode}")
        if item.pinned:
            lines.append("📌 Pinned")
        if item.favorite:
            lines.append("⭐ Favorite")
        lines.append("---\n")
    return Response(content="\n".join(lines), media_type="text/markdown", headers={"Content-Disposition": "attachment; filename=sightlineai_history.md"})


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------

@app.post("/api/session-history/favorite")
def favorite_history_item(request: FavoriteRequest) -> dict:
    """Mark a history item as favorite."""
    item = history_store.favorite(request.item_id)
    if not item:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": f"Item {request.item_id} not found"})
    return {"favorited": True, "item_id": request.item_id}


@app.post("/api/session-history/unfavorite")
def unfavorite_history_item(request: FavoriteRequest) -> dict:
    """Remove favorite from a history item."""
    item = history_store.unfavorite(request.item_id)
    if not item:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": f"Item {request.item_id} not found"})
    return {"unfavorited": True, "item_id": request.item_id}


@app.get("/api/session-history/favorites", response_model=SessionHistoryResponse)
def list_favorites() -> SessionHistoryResponse:
    """List all favorited history items."""
    items = [item for item in history_store.list_items() if item.favorite]
    return SessionHistoryResponse(items=items)


# ---------------------------------------------------------------------------
# Conversation endpoint
# ---------------------------------------------------------------------------

@app.post("/api/conversation", response_model=ConversationResponse)
def conversation(request: ConversationRequest) -> ConversationResponse:
    """Maintain conversation context across multiple guidance requests."""
    session_id = request.session_id or str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    session = conversation_store.get(session_id, {
        "messages": [],
        "created_at": now,
        "updated_at": now,
    })

    session["messages"].append({"role": "user", "content": request.message})
    conversation_messages = session["messages"][-10:]

    try:
        fallback_reason = None
        response = qwen_client.get_guidance(
            scene_description=request.message,
            geospatial_context=request.geospatial_context,
            language=request.language,
            conversation_messages=conversation_messages[:-1],
        )
        response.risk_score = compute_geospatial_risk(request.geospatial_context)
    except MissingAPIKeyError:
        fallback_reason = "missing_api_key"
    except UpstreamAPIError:
        fallback_reason = "upstream_unavailable"
    except QwenClientError:
        fallback_reason = "qwen_parse_error"

    if fallback_reason:
        response = build_fallback_guidance(
            scene_description=request.message,
            geospatial_context=request.geospatial_context,
            reason=fallback_reason,
            language=request.language,
        )

    session["messages"].append({"role": "assistant", "content": response.guidance_text})
    session["updated_at"] = now
    conversation_store[session_id] = session

    return ConversationResponse(
        session_id=session_id,
        reply=response,
        message_count=len(session["messages"]),
    )


@app.get("/api/conversation/{session_id}")
def get_conversation(session_id: str) -> dict:
    """Get conversation history for a session."""
    session = conversation_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": f"Conversation {session_id} not found"})
    return {"session_id": session_id, **session}


@app.delete("/api/conversation/{session_id}")
def delete_conversation(session_id: str) -> dict[str, bool]:
    """Delete a conversation session."""
    if session_id not in conversation_store:
        raise HTTPException(status_code=404, detail={"error": "not_found", "detail": f"Conversation {session_id} not found"})
    del conversation_store[session_id]
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Accessibility Score
# ---------------------------------------------------------------------------

OBSTACLE_KEYWORDS = {
    "wall": 0.3, "barrier": 0.4, "fence": 0.3, "construction": 0.5,
    "stairs": 0.4, "steps": 0.3, "curb": 0.2, "door": 0.15,
    "gate": 0.2, "pole": 0.2, "post": 0.2, "pillar": 0.25,
    "vehicle": 0.4, "car": 0.35, "bus": 0.4, "truck": 0.4,
    "bicycle": 0.25, "scooter": 0.25, "crowd": 0.3, "people": 0.2,
}

PATH_CLEAR_KEYWORDS = {
    "open": 0.3, "clear": 0.3, "wide": 0.2, "straight": 0.2,
    "smooth": 0.2, "flat": 0.15, "path": 0.1, "sidewalk": 0.15,
    "corridor": 0.1, "hallway": 0.1,
}

SENSORY_CUE_MAP = {
    "traffic": "traffic sounds for orientation",
    "wind": "wind direction as directional cue",
    "water": "water sound as landmark",
    "music": "audio landmark from music",
    "voice": "human voice proximity",
    "engine": "engine sound for vehicle detection",
    "bird": "ambient nature sound",
    "bell": "bell/chime as landmark",
    "tactile": "tactile paving indicator",
    "handrail": "handrail for physical guidance",
    "curb": "curb edge detection",
    "slope": "slope gradient feedback",
    "echo": "echo for spatial awareness",
}


@app.post("/api/accessibility-score", response_model=AccessibilityScoreResponse)
def accessibility_score(request: AccessibilityScoreRequest) -> AccessibilityScoreResponse:
    """Analyze a scene description for accessibility scoring."""
    text = request.scene_description.lower()

    obstacle_score = sum(weight for keyword, weight in OBSTACLE_KEYWORDS.items() if keyword in text)
    obstacle_density = min(obstacle_score, 1.0)

    path_score = sum(weight for keyword, weight in PATH_CLEAR_KEYWORDS.items() if keyword in text)
    path_clarity = min(path_score, 1.0)

    sensory_cues = [desc for keyword, desc in SENSORY_CUE_MAP.items() if keyword in text]
    if not sensory_cues:
        sensory_cues = ["No specific sensory cues mentioned — proceed with caution"]

    raw = (1.0 - obstacle_density) * 50 + path_clarity * 30 + min(len(sensory_cues) * 5, 20)
    overall = max(10, min(int(raw), 100))

    recommendations = []
    if obstacle_density > 0.3:
        recommendations.append("High obstacle density detected — use cane sweep before each step")
    if path_clarity < 0.2:
        recommendations.append("Path clarity unclear — pause and probe surroundings before moving")
    if not sensory_cues or sensory_cues == ["No specific sensory cues mentioned — proceed with caution"]:
        recommendations.append("No sensory cues identified — rely on tactile and cane feedback")
    if overall < 40:
        recommendations.append("Low accessibility score — consider finding an alternative route")
    if not recommendations:
        recommendations.append("Scene appears moderately accessible — maintain standard caution")

    return AccessibilityScoreResponse(
        obstacle_density=round(obstacle_density, 2),
        path_clarity=round(path_clarity, 2),
        sensory_cues=sensory_cues,
        overall_score=overall,
        recommendations=recommendations,
    )


# ---------------------------------------------------------------------------
# Settings endpoint
# ---------------------------------------------------------------------------

@app.get("/api/settings", response_model=AppSettings)
def get_app_settings() -> AppSettings:
    """Return current application settings."""
    return AppSettings(
        model=settings.qwen_model,
        version=settings.app_version,
        timeout=settings.request_timeout_seconds,
        persist_history=os.getenv("PERSIST_HISTORY", "false").lower() in ("true", "1"),
        features={
            "vision_api": True,
            "conversation": True,
            "multilingual": True,
            "websocket": True,
            "favorites": True,
            "accessibility_score": True,
        },
    )


@app.post("/api/settings")
def update_app_settings(request: UpdateSettingsRequest) -> dict:
    """Update runtime settings."""
    if request.model:
        settings.qwen_model = request.model
        qwen_client._settings = settings
    if request.timeout:
        settings.request_timeout_seconds = request.timeout
        qwen_client._settings = settings
    return {"updated": True, "model": settings.qwen_model, "timeout": settings.request_timeout_seconds}


# ---------------------------------------------------------------------------
# WebSocket streaming endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws/guidance")
async def ws_guidance(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming guidance responses."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            scene = data.get("scene_description", "")
            language = data.get("language", "en")
            geo = data.get("geospatial_context")

            geospatial_context = GeospatialContext(**geo) if geo else None

            if not scene or len(scene) < 5:
                await websocket.send_json({"error": "scene_description too short"})
                continue

            try:
                full_content = ""
                for token in qwen_client.stream_guidance(
                    scene_description=scene,
                    geospatial_context=geospatial_context,
                    language=language,
                ):
                    full_content += token
                    await websocket.send_json({"type": "token", "content": token})

                from app.utils import extract_json_object, normalize_guidance_payload
                parsed = extract_json_object(full_content)
                result = normalize_guidance_payload(parsed)
                result.risk_score = compute_geospatial_risk(geospatial_context)
                await websocket.send_json({"type": "done", "response": result.model_dump()})

            except (MissingAPIKeyError, UpstreamAPIError, QwenClientError):
                response = build_fallback_guidance(
                    scene_description=scene,
                    geospatial_context=geospatial_context,
                    reason="streaming_fallback",
                    language=language,
                )
                await websocket.send_json({"type": "done", "response": response.model_dump()})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass



# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

_sensor_adapter = SensorAdapter()


def get_current_user(request: Request) -> dict | None:
    """Extract and verify Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    payload = verify_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = _get_user(user_id)
    return user


# ---------------------------------------------------------------------------
# OCR endpoint
# ---------------------------------------------------------------------------

@app.post("/api/ocr", response_model=OCRResponse)
async def ocr_extract(image: UploadFile = File(...)) -> OCRResponse:
    """Extract text from an uploaded image using OCR."""
    content_parts: list[bytes] = []
    while True:
        chunk = await image.read(1024 * 256)
        if not chunk:
            break
        content_parts.append(chunk)
    content = b"".join(content_parts)

    result = extract_text_with_metadata(content)
    if not result.get("available"):
        return OCRResponse(text="", available=False, error=result.get("error", "pytesseract not installed"))
    if result.get("error"):
        return OCRResponse(text="", available=True, error=result["error"])
    return OCRResponse(text=result.get("text", ""), available=True)


# ---------------------------------------------------------------------------
# Map endpoints
# ---------------------------------------------------------------------------

@app.post("/api/map/search", response_model=LocationSearchResponse)
def map_search(request: LocationSearchRequest) -> LocationSearchResponse:
    """Search for locations using Nominatim geocoding."""
    from app.schemas import LocationResult
    results = _search_location(request.query, request.limit)
    return LocationSearchResponse(
        results=[LocationResult(**r) for r in results]
    )


@app.post("/api/map/route", response_model=RouteResponse)
def map_route(request: RouteRequest) -> RouteResponse:
    """Get a walking route with accessibility notes via OSRM."""
    from app.schemas import RouteStep
    result = _get_route(
        origin=(request.origin_lat, request.origin_lon),
        destination=(request.dest_lat, request.dest_lon),
    )
    if not result.get("available"):
        return RouteResponse(available=False, error=result.get("error", "Route not found"))
    steps = [RouteStep(**s) for s in result.get("steps", [])]
    return RouteResponse(
        available=True,
        distance_m=result.get("distance_m", 0),
        duration_s=result.get("duration_s", 0),
        geometry=result.get("geometry", {}),
        steps=steps,
        accessibility_notes=result.get("accessibility_notes", []),
    )


@app.post("/api/map/nearby-hazards", response_model=NearbyHazardsResponse)
def map_nearby_hazards(request: NearbyHazardsRequest) -> NearbyHazardsResponse:
    """Get nearby accessibility hazards from OpenStreetMap."""
    from app.schemas import HazardItem
    result = _get_nearby_hazards(request.lat, request.lon, request.radius)
    hazards = [HazardItem(**h) for h in result.get("hazards", [])]
    return NearbyHazardsResponse(
        available=result.get("available", False),
        count=result.get("count", 0),
        hazards=hazards,
        error=result.get("error"),
    )


@app.post("/api/map/accessibility-tiles", response_model=AccessibilityTilesResponse)
def map_accessibility_tiles(request: AccessibilityTilesRequest) -> AccessibilityTilesResponse:
    """Get OSM accessibility features nearby."""
    from app.schemas import AccessibilityFeature
    result = _get_accessibility_tiles(request.lat, request.lon, request.radius)
    features = [AccessibilityFeature(**f) for f in result.get("features", [])]
    return AccessibilityTilesResponse(
        available=result.get("available", False),
        count=result.get("count", 0),
        features=features,
        error=result.get("error"),
    )


# ---------------------------------------------------------------------------
# Sensor endpoints
# ---------------------------------------------------------------------------

@app.post("/api/sensor/reading", response_model=SensorReadingResponse)
def sensor_reading(request: SensorReadingRequest) -> SensorReadingResponse:
    """Submit a sensor reading for processing."""
    processor_map = {
        "lidar": _sensor_adapter.process_lidar,
        "imu": _sensor_adapter.process_imu,
        "depth": _sensor_adapter.process_depth,
        "gps": _sensor_adapter.process_gps,
    }
    processor = processor_map.get(request.sensor_type)
    if not processor:
        return SensorReadingResponse(processed=False, sensor_type=request.sensor_type, error=f"Unknown sensor type: {request.sensor_type}")
    result = processor(request.data)
    if not result.get("processed"):
        return SensorReadingResponse(processed=False, sensor_type=request.sensor_type, error=result.get("error", "Processing failed"))
    return SensorReadingResponse(processed=True, sensor_type=request.sensor_type, result=result)


@app.post("/api/sensor/fusion", response_model=SensorFusionResponse)
def sensor_fusion(request: SensorFusionRequest) -> SensorFusionResponse:
    """Submit multiple sensor readings for fusion analysis."""
    processed_readings = []
    for r in request.readings:
        processor_map = {
            "lidar": _sensor_adapter.process_lidar,
            "imu": _sensor_adapter.process_imu,
            "depth": _sensor_adapter.process_depth,
            "gps": _sensor_adapter.process_gps,
        }
        processor = processor_map.get(r.sensor_type)
        if processor:
            result = processor(r.data)
            if result.get("processed"):
                processed_readings.append(result)

    fusion = compute_sensor_fusion(processed_readings)
    guidance = generate_sensor_guidance(fusion)

    return SensorFusionResponse(
        risk_score=fusion["risk_score"],
        risk_level=fusion["risk_level"],
        sensor_count=fusion["sensor_count"],
        sensor_types=fusion["sensor_types"],
        factors=fusion["factors"],
        guidance=guidance,
    )


@app.post("/api/sensor/guidance")
def sensor_guidance(request: SensorFusionRequest) -> dict:
    """Get guidance directly from sensor data."""
    processed_readings = []
    for r in request.readings:
        processor_map = {
            "lidar": _sensor_adapter.process_lidar,
            "imu": _sensor_adapter.process_imu,
            "depth": _sensor_adapter.process_depth,
            "gps": _sensor_adapter.process_gps,
        }
        processor = processor_map.get(r.sensor_type)
        if processor:
            result = processor(r.data)
            if result.get("processed"):
                processed_readings.append(result)

    fusion = compute_sensor_fusion(processed_readings)
    return generate_sensor_guidance(fusion)


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.post("/api/auth/register", response_model=TokenResponse)
def auth_register(request: UserRegister) -> TokenResponse:
    """Register a new user."""
    try:
        user = _register_user(email=request.email, password=request.password, name=request.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "registration_failed", "detail": str(exc)}) from exc
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user["id"], email=user["email"], name=user["name"]),
    )


@app.post("/api/auth/login", response_model=TokenResponse)
def auth_login(request: UserLogin) -> TokenResponse:
    """Login and receive a JWT token."""
    user = _authenticate_user(email=request.email, password=request.password)
    if not user:
        raise HTTPException(status_code=401, detail={"error": "invalid_credentials", "detail": "Invalid email or password"})
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user["id"], email=user["email"], name=user["name"]),
    )


@app.get("/api/auth/me", response_model=UserResponse)
def auth_me(request: Request) -> UserResponse:
    """Get current user profile (requires auth)."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail={"error": "unauthorized", "detail": "Valid Bearer token required"})
    return UserResponse(id=user["id"], email=user["email"], name=user["name"])


@app.post("/api/auth/logout")
def auth_logout(request: Request) -> dict[str, bool]:
    """Invalidate the current token."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        invalidate_token(auth_header[7:])
    return {"logged_out": True}


# ---------------------------------------------------------------------------
# Static file serving
# ---------------------------------------------------------------------------
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


@app.get("/")
def root() -> FileResponse:
    index_file = (frontend_dir / "index.html").resolve()
    if frontend_dir.resolve() not in index_file.parents and index_file != frontend_dir.resolve() / "index.html":
        raise HTTPException(status_code=403, detail={"error": "forbidden", "detail": "Path traversal denied"})
    if index_file.exists():
        return FileResponse(index_file, headers={"Content-Disposition": "inline"})
    raise HTTPException(status_code=404, detail={"error": "not_found", "detail": "Frontend not found"})
