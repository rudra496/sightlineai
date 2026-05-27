from __future__ import annotations

import base64
import logging
import re

import filetype
from fastapi import UploadFile

from app.config import get_settings
from app.qwen_client import MissingAPIKeyError, QwenClient, QwenClientError, UpstreamAPIError
from app.schemas import GeospatialContext, ImageAnalysisResponse
from app.services.fallback_guidance import build_fallback_guidance
from app.services.ocr_service import extract_text as _attempt_ocr, is_ocr_available as _check_ocr_available
from app.prompts import FALLBACK_TEMPLATES_BN

logger = logging.getLogger("sightlineai.image_analysis")

ALLOWED_IMAGE_TYPES = {"jpg", "jpeg", "png", "webp"}


# --- Brightness Estimation (pure Python, no PIL) ---

def _estimate_brightness(content: bytes) -> str:
    """Estimate image brightness from raw byte values."""
    if len(content) < 100:
        return "unknown"

    sample_positions = list(range(0, len(content), max(len(content) // 50, 1)))
    sample_positions = sample_positions[:50]
    sampled = [content[i] for i in sample_positions]
    avg = sum(sampled) / len(sampled)

    if avg < 50:
        return "very_dark"
    if avg < 100:
        return "dark"
    if avg < 160:
        return "moderate"
    if avg < 210:
        return "bright"
    return "very_bright"


def _extract_filename_tokens(filename: str | None) -> str:
    if not filename:
        return ""
    clean = re.sub(r"[^a-zA-Z0-9]+", " ", filename).strip()
    return clean[:120]


def _build_filename_description(filename: str | None) -> str:
    """Generate a more descriptive fallback based on filename analysis."""
    if not filename:
        return "No filename provided."
    tokens = _extract_filename_tokens(filename).lower()
    descriptions = []
    if "outdoor" in tokens or "outside" in tokens:
        descriptions.append("outdoor scene")
    if "indoor" in tokens or "inside" in tokens:
        descriptions.append("indoor scene")
    if "street" in tokens or "road" in tokens:
        descriptions.append("street or road environment")
    if "room" in tokens:
        descriptions.append("room interior")
    if "door" in tokens or "entrance" in tokens:
        descriptions.append("doorway or entrance area")
    if "stair" in tokens or "step" in tokens:
        descriptions.append("stairs or steps present")
    if "sign" in tokens:
        descriptions.append("contains signage")
    if descriptions:
        return f"Filename suggests: {', '.join(descriptions)}. "
    return f"Filename: {filename}. "


async def analyze_uploaded_image(
    file: UploadFile,
    geospatial_context: GeospatialContext | None,
    text_hint: str | None,
    max_bytes: int,
    qwen_client: QwenClient | None = None,
    language: str = "en",
) -> ImageAnalysisResponse:
    content_parts: list[bytes] = []
    total_bytes = 0
    while True:
        chunk = await file.read(1024 * 256)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise ValueError(f"Image exceeds max size of {max_bytes} bytes")
        content_parts.append(chunk)

    content = b"".join(content_parts)
    guess = filetype.guess(content)
    image_kind = guess.extension if guess else None
    if image_kind not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Unsupported image type. Use PNG, JPEG, or WEBP")

    # --- Try Qwen Vision API first ---
    if qwen_client and qwen_client.has_api_key and not qwen_client.circuit_open:
        try:
            image_b64 = base64.b64encode(content).decode("utf-8")
            guidance = qwen_client.get_image_guidance(
                image_base64=image_b64,
                text_hint=text_hint,
                geospatial_context=geospatial_context,
                language=language,
            )
            summary_parts = [
                f"Analyzed via Qwen Vision ({image_kind.upper()}, {len(content)} bytes).",
                text_hint or "",
            ]
            image_summary = " ".join(p for p in summary_parts if p).strip()

            # OCR attempt for extracted text.
            ocr_text = _attempt_ocr(content)
            if ocr_text:
                extracted_text = ocr_text
            elif _check_ocr_available():
                extracted_text = "OCR was attempted but no text was detected."
            else:
                extracted_text = "OCR is not available (pytesseract not installed)."

            return ImageAnalysisResponse(
                **guidance.model_dump(),
                image_summary=image_summary,
                extracted_text=extracted_text,
            )
        except (QwenClientError, Exception) as exc:
            logger.warning("Qwen vision failed, falling back to heuristic: %s", exc)

    # --- Fallback: heuristic analysis ---
    brightness = _estimate_brightness(content)

    size_kb = len(content) / 1024
    if size_kb < 50:
        dims_hint = "small (<50KB, likely thumbnail)"
    elif size_kb < 200:
        dims_hint = "medium (50-200KB)"
    elif size_kb < 1000:
        dims_hint = "large (200KB-1MB)"
    else:
        dims_hint = "very large (>1MB, high-res)"

    ocr_text = _attempt_ocr(content)
    if ocr_text is None:
        if _check_ocr_available():
            extracted_text = "OCR was attempted but no text was detected."
        else:
            extracted_text = "OCR is not available (pytesseract not installed)."
    else:
        extracted_text = ocr_text

    filename_tokens = _extract_filename_tokens(file.filename)
    filename_desc = _build_filename_description(file.filename)
    brightness_note = f"Brightness: {brightness}." if brightness != "unknown" else ""
    ocr_note = f" OCR detected text: {ocr_text}" if ocr_text else ""

    assembled_parts = [text_hint or "", filename_tokens, brightness_note, ocr_note]
    assembled_scene = " ".join(part for part in assembled_parts if part).strip()
    if not assembled_scene:
        assembled_scene = "Image uploaded with no descriptive hint."

    guidance = build_fallback_guidance(
        scene_description=assembled_scene,
        geospatial_context=geospatial_context,
        reason="image_fallback_pipeline",
        language=language,
    )

    summary_parts = [
        f"Validated {image_kind.upper()} image ({len(content)} bytes, {dims_hint}).",
        filename_desc.strip(),
        brightness_note,
    ]
    image_summary = " ".join(part for part in summary_parts if part).strip()

    return ImageAnalysisResponse(
        **guidance.model_dump(),
        image_summary=image_summary,
        extracted_text=extracted_text,
    )
