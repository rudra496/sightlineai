from __future__ import annotations

import os
import warnings
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

    def validate(self) -> list[str]:
        """Return a list of warning messages for suspicious config values."""
        warnings_list: list[str] = []
        if not self.dashscope_api_key:
            warnings_list.append("DASHSCOPE_API_KEY is not set; API calls will fall back to offline mode.")
        if self.request_timeout_seconds > 60:
            warnings_list.append(f"request_timeout_seconds={self.request_timeout_seconds}s is very high (>60s).")
        if self.request_timeout_seconds < 5:
            warnings_list.append(f"request_timeout_seconds={self.request_timeout_seconds}s is very low (<5s), may cause frequent timeouts.")
        if self.image_max_bytes > 20 * 1024 * 1024:
            warnings_list.append(f"image_max_bytes={self.image_max_bytes} exceeds 20MB; large uploads may hurt performance.")
        if not self.dashscope_base_url.startswith("https://"):
            warnings_list.append(f"dashscope_base_url is not HTTPS: {self.dashscope_base_url}")
        return warnings_list


_cached_settings: Settings | None = None


def get_settings() -> Settings:
    """Return cached Settings singleton. Env is parsed only once."""
    global _cached_settings
    if _cached_settings is not None:
        return _cached_settings

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

    _cached_settings = Settings(
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        dashscope_base_url=os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        ),
        qwen_model=os.getenv("QWEN_MODEL", "qwen3.7-max"),
        request_timeout_seconds=max(timeout, 1.0),
        image_max_bytes=max(1024 * 100, max_image_bytes),
    )

    for w in _cached_settings.validate():
        warnings.warn(w, stacklevel=2)

    return _cached_settings
