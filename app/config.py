from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = "SightlineAI"
    app_version: str = "0.2.0"
    dashscope_api_key: str | None = None
    dashscope_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen3.7-max"
    request_timeout_seconds: float = 25.0
    image_max_bytes: int = 5 * 1024 * 1024


def get_settings() -> Settings:
    timeout_raw = os.getenv("QWEN_TIMEOUT_SECONDS", "25")
    max_image_raw = os.getenv("MAX_IMAGE_BYTES", str(5 * 1024 * 1024))

    try:
        timeout = float(timeout_raw)
    except ValueError:
        timeout = 25.0

    try:
        max_image_bytes = int(max_image_raw)
    except ValueError:
        max_image_bytes = 5 * 1024 * 1024

    return Settings(
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        dashscope_base_url=os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        ),
        qwen_model=os.getenv("QWEN_MODEL", "qwen3.7-max"),
        request_timeout_seconds=max(timeout, 1.0),
        image_max_bytes=max(1024 * 100, max_image_bytes),
    )
