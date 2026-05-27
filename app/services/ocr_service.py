from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("sightlineai.ocr")

_OCR_AVAILABLE: bool | None = None


def is_ocr_available() -> bool:
    """Check if pytesseract is available at runtime."""
    global _OCR_AVAILABLE
    if _OCR_AVAILABLE is not None:
        return _OCR_AVAILABLE
    try:
        import pytesseract  # noqa: F401
        _OCR_AVAILABLE = True
    except ImportError:
        _OCR_AVAILABLE = False
    return _OCR_AVAILABLE


def extract_text(content: bytes) -> str | None:
    """Extract text from image bytes using pytesseract. Returns None if OCR unavailable."""
    if not is_ocr_available():
        return None
    try:
        import pytesseract
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(img).strip()
        return text if text else None
    except Exception:
        return None


def extract_text_with_metadata(content: bytes) -> dict[str, Any]:
    """Extract text and return structured result with metadata."""
    if not is_ocr_available():
        return {"available": False, "text": None, "error": "pytesseract not installed"}

    try:
        import pytesseract
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(img).strip()
        return {
            "available": True,
            "text": text if text else "",
            "confidence": None,
            "image_size": img.size,
        }
    except Exception as exc:
        return {"available": True, "text": None, "error": str(exc)}
