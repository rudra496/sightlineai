from __future__ import annotations

import imghdr
import re
from fastapi import UploadFile

from app.schemas import GeospatialContext, ImageAnalysisResponse
from app.services.fallback_guidance import build_fallback_guidance

ALLOWED_IMAGE_TYPES = {"jpeg", "png", "webp"}


def _extract_filename_tokens(filename: str | None) -> str:
    if not filename:
        return ""
    clean = re.sub(r"[^a-zA-Z0-9]+", " ", filename).strip()
    return clean[:120]


async def analyze_uploaded_image(
    file: UploadFile,
    geospatial_context: GeospatialContext | None,
    text_hint: str | None,
    max_bytes: int,
) -> ImageAnalysisResponse:
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ValueError(f"Image exceeds max size of {max_bytes} bytes")

    image_kind = imghdr.what(None, h=content)
    if image_kind not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Unsupported image type. Use PNG, JPEG, or WEBP")

    filename_tokens = _extract_filename_tokens(file.filename)
    assembled_scene = " ".join(part for part in [text_hint or "", filename_tokens] if part).strip()
    if not assembled_scene:
        assembled_scene = "Image uploaded with no descriptive hint."

    guidance = build_fallback_guidance(
        scene_description=assembled_scene,
        geospatial_context=geospatial_context,
        reason="image_fallback_pipeline",
    )

    return ImageAnalysisResponse(
        **guidance.model_dump(),
        image_summary=f"Validated {image_kind.upper()} image ({len(content)} bytes).",
        extracted_text="OCR is not enabled in this MVP fallback pipeline.",
    )
