from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.qwen_client import MissingAPIKeyError, QwenClient, QwenClientError, UpstreamAPIError
from app.schemas import ErrorResponse, GuidanceRequest, GuidanceResponse

settings = get_settings()
qwen_client = QwenClient(settings)

app = FastAPI(
    title="SightlineAI API",
    version=settings.app_version,
    description="Accessibility-focused environmental guidance API powered by Qwen.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_input",
            "detail": "scene_description is required and must be a non-empty string.",
            "validation": exc.errors(),
        },
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "model": settings.qwen_model}


@app.post(
    "/api/guidance",
    response_model=GuidanceResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def guidance(request: GuidanceRequest) -> GuidanceResponse:
    try:
        return qwen_client.get_guidance(request.scene_description)
    except MissingAPIKeyError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "configuration_error",
                "detail": str(exc),
            },
        ) from exc
    except UpstreamAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "upstream_api_error",
                "detail": str(exc),
            },
        ) from exc
    except QwenClientError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "qwen_client_error",
                "detail": str(exc),
            },
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "detail": "Unexpected server error",
            },
        ) from exc


frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


@app.get("/")
def root() -> FileResponse:
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail={"error": "not_found", "detail": "Frontend not found"})
