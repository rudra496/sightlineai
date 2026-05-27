from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.qwen_client import MissingAPIKeyError, QwenClient, QwenClientError, UpstreamAPIError
from app.schemas import (
    EdgeContextRequest,
    EdgeContextResponse,
    ErrorResponse,
    FallbackGuidanceRequest,
    GeospatialContext,
    GuidanceRequest,
    GuidanceResponse,
    ImageAnalysisResponse,
    SessionHistoryCreateRequest,
    SessionHistoryItem,
    SessionHistoryResponse,
)
from app.services.edge_context import evaluate_edge_context
from app.services.fallback_guidance import build_fallback_guidance
from app.services.geospatial import compute_geospatial_risk
from app.services.history_store import SessionHistoryStore
from app.services.image_analysis import analyze_uploaded_image

settings = get_settings()
qwen_client = QwenClient(settings)
history_store = SessionHistoryStore()

app = FastAPI(
    title="SightlineAI API",
    version=settings.app_version,
    description="Accessibility-first guidance API with Qwen + offline fallback + image/edge context support.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


def _error_payload(request: Request, error: str, detail: str) -> dict[str, str]:
    return {"error": error, "detail": detail, "request_id": getattr(request.state, "request_id", None)}


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            **_error_payload(
                request,
                "invalid_input",
                "Request body failed validation. Check required fields and data types.",
            ),
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


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "model": settings.qwen_model,
        "fallback": "enabled",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post(
    "/api/guidance",
    response_model=GuidanceResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def guidance(request: GuidanceRequest) -> GuidanceResponse:
    fallback_reason: str | None = None
    try:
        response = qwen_client.get_guidance(request.scene_description, request.geospatial_context)
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
    )
    history_store.add_from_guidance(source="fallback", scene=request.scene_description, response=response)
    return response


@app.post("/api/edge-context", response_model=EdgeContextResponse)
def edge_context(request: EdgeContextRequest) -> EdgeContextResponse:
    return evaluate_edge_context(request)


@app.post(
    "/api/analyze-image",
    response_model=ImageAnalysisResponse,
    responses={400: {"model": ErrorResponse}},
)
async def analyze_image(
    image: UploadFile = File(...),
    location_label: str | None = Form(default=None),
    route_description: str | None = Form(default=None),
    text_hint: str | None = Form(default=None),
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
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_image", "detail": str(exc)},
        ) from exc

    history_store.add_from_guidance(source="image", scene=text_hint or "Image upload", response=response)
    return response


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


@app.delete("/api/session-history")
def clear_session_history() -> dict[str, bool]:
    history_store.clear()
    return {"cleared": True}


frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


@app.get("/")
def root() -> FileResponse:
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail={"error": "not_found", "detail": "Frontend not found"})
