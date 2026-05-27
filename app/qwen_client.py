from __future__ import annotations

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

from app.config import Settings
from app.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas import GuidanceResponse
from app.utils import extract_json_object, normalize_guidance_payload


class QwenClientError(Exception):
    """Base Qwen client error."""


class MissingAPIKeyError(QwenClientError):
    """Raised when API key is not available."""


class UpstreamAPIError(QwenClientError):
    """Raised when the upstream API fails."""


class QwenClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def has_api_key(self) -> bool:
        return bool(self._settings.dashscope_api_key)

    def get_guidance(self, scene_description: str) -> GuidanceResponse:
        if not self._settings.dashscope_api_key:
            raise MissingAPIKeyError(
                "Missing DASHSCOPE_API_KEY. Set it in your environment before running the API."
            )

        url = f"{self._settings.dashscope_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self._settings.qwen_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(scene_description)},
            ],
            "temperature": 0.2,
            "max_tokens": 320,
        }
        headers = {
            "Authorization": "Bearer " + self._settings.dashscope_api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self._settings.request_timeout_seconds,
            )
        except Timeout as exc:
            raise UpstreamAPIError("Qwen API request timed out") from exc
        except RequestException as exc:
            raise UpstreamAPIError("Network failure while contacting Qwen API") from exc

        self._raise_for_status(response)

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise UpstreamAPIError("Unexpected response format from Qwen API") from exc

        parsed = extract_json_object(content)
        return normalize_guidance_payload(parsed)

    @staticmethod
    def _raise_for_status(response: Response) -> None:
        if response.status_code < 400:
            return

        detail = "Qwen API returned an error"
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                message = error_data.get("error", {}).get("message")
                if isinstance(message, str) and message.strip():
                    detail = message
        except ValueError:
            pass

        raise UpstreamAPIError(f"{detail} (status {response.status_code})")
