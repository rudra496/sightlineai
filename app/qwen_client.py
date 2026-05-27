from __future__ import annotations

import logging
import time

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

from app.config import Settings
from app.prompts import SYSTEM_PROMPT, build_user_prompt, get_system_prompt
from app.schemas import GeospatialContext, GuidanceResponse
from app.utils import extract_json_object, normalize_guidance_payload

logger = logging.getLogger("sightlineai.qwen")


class QwenClientError(Exception):
    """Base Qwen client error."""


class MissingAPIKeyError(QwenClientError):
    """Raised when API key is not available."""


class UpstreamAPIError(QwenClientError):
    """Raised when the upstream API fails."""


# Maximum number of retries for transient failures.
MAX_RETRIES = 2
# Base delay in seconds for exponential backoff.
BASE_RETRY_DELAY = 1.0

# Circuit breaker thresholds.
CB_FAILURE_THRESHOLD = 3
CB_COOLDOWN_SECONDS = 30.0


def _is_retryable(exc: Exception) -> bool:
    """Return True for transient errors that warrant a retry."""
    if isinstance(exc, Timeout):
        return True
    if isinstance(exc, UpstreamAPIError):
        msg = str(exc).lower()
        if "status 5" in msg or "timed out" in msg:
            return True
        return False
    return False


class QwenClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        # Connection pooling via requests.Session (reuses TCP connections).
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})
        # Circuit breaker state.
        self._consecutive_failures = 0
        self._cb_open_until: float = 0.0

    def close(self) -> None:
        """Clean up the underlying session (call on shutdown)."""
        self._session.close()

    @property
    def has_api_key(self) -> bool:
        return bool(self._settings.dashscope_api_key)

    @property
    def circuit_open(self) -> bool:
        """Return True if the circuit breaker is tripped."""
        return time.monotonic() < self._cb_open_until

    def _record_success(self) -> None:
        self._consecutive_failures = 0

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= CB_FAILURE_THRESHOLD:
            self._cb_open_until = time.monotonic() + CB_COOLDOWN_SECONDS
            logger.warning("Circuit breaker OPEN – skipping direct attempts for %.0fs", CB_COOLDOWN_SECONDS)

    def get_guidance(
        self,
        scene_description: str,
        geospatial_context: GeospatialContext | None = None,
        language: str = "en",
        conversation_messages: list[dict] | None = None,
    ) -> GuidanceResponse:
        if not self._settings.dashscope_api_key:
            raise MissingAPIKeyError(
                "Missing DASHSCOPE_API_KEY. Set it in your environment before running the API."
            )

        # Circuit breaker check: if open, fail fast.
        if self.circuit_open:
            raise UpstreamAPIError(
                f"Circuit breaker open – {self._consecutive_failures} consecutive failures. "
                f"Retrying after {self._cb_open_until - time.monotonic():.0f}s."
            )

        url = f"{self._settings.dashscope_base_url.rstrip('/')}/chat/completions"

        system_prompt = get_system_prompt(language)
        messages: list[dict] = [{"role": "system", "content": system_prompt}]

        # Add conversation context if provided.
        if conversation_messages:
            messages.extend(conversation_messages)

        messages.append({
            "role": "user",
            "content": build_user_prompt(
                scene_description=scene_description,
                geospatial_context=geospatial_context,
            ),
        })

        payload = {
            "model": self._settings.qwen_model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 320,
        }
        headers = {
            "Authorization": "Bearer " + self._settings.dashscope_api_key,
        }

        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self._session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self._settings.request_timeout_seconds,
                )
                self._raise_for_status(response)

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                parsed = extract_json_object(content)
                result = normalize_guidance_payload(parsed)
                self._record_success()
                return result

            except (Timeout, RequestException) as exc:
                last_exc = exc
            except UpstreamAPIError as exc:
                last_exc = exc
                if not _is_retryable(exc):
                    self._record_failure()
                    raise
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                self._record_failure()
                raise UpstreamAPIError("Unexpected response format from Qwen API") from exc

            # Retryable failure — exponential backoff
            if attempt < MAX_RETRIES:
                delay = BASE_RETRY_DELAY * (2 ** attempt)
                time.sleep(delay)

        # All retries exhausted
        self._record_failure()
        if isinstance(last_exc, Timeout):
            raise UpstreamAPIError("Qwen API request timed out after retries") from last_exc
        if isinstance(last_exc, UpstreamAPIError):
            raise last_exc
        raise UpstreamAPIError("Network failure while contacting Qwen API after retries") from last_exc

    def get_image_guidance(
        self,
        image_base64: str,
        text_hint: str | None = None,
        geospatial_context: GeospatialContext | None = None,
        language: str = "en",
    ) -> GuidanceResponse:
        """Send an image to Qwen's vision model for accessibility guidance."""
        if not self._settings.dashscope_api_key:
            raise MissingAPIKeyError("Missing DASHSCOPE_API_KEY for image analysis.")

        if self.circuit_open:
            raise UpstreamAPIError("Circuit breaker open – cannot process image.")

        url = f"{self._settings.dashscope_base_url.rstrip('/')}/chat/completions"

        system_prompt = get_system_prompt(language)
        # Build multimodal message content
        image_url = f"data:image/jpeg;base64,{image_base64}"
        content_parts: list[dict] = [
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
        if text_hint:
            content_parts.append({
                "type": "text",
                "text": text_hint,
            })
        else:
            content_parts.append({
                "type": "text",
                "text": "Analyze this image for accessibility guidance for a blind or visually impaired user.",
            })

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_parts},
        ]

        payload = {
            "model": self._settings.qwen_model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 400,
        }
        headers = {
            "Authorization": "Bearer " + self._settings.dashscope_api_key,
        }

        try:
            response = self._session.post(
                url,
                headers=headers,
                json=payload,
                timeout=self._settings.request_timeout_seconds,
            )
            self._raise_for_status(response)
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = extract_json_object(content)
            result = normalize_guidance_payload(parsed)
            self._record_success()
            return result
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            self._record_failure()
            raise UpstreamAPIError("Unexpected response format from Qwen vision API") from exc
        except (Timeout, RequestException) as exc:
            self._record_failure()
            raise UpstreamAPIError("Network failure in Qwen vision API") from exc

    def stream_guidance(
        self,
        scene_description: str,
        geospatial_context: GeospatialContext | None = None,
        language: str = "en",
    ):
        """Stream Qwen responses token by token. Yields content strings."""
        if not self._settings.dashscope_api_key:
            raise MissingAPIKeyError("Missing DASHSCOPE_API_KEY.")

        url = f"{self._settings.dashscope_base_url.rstrip('/')}/chat/completions"

        system_prompt = get_system_prompt(language)
        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": build_user_prompt(
                    scene_description=scene_description,
                    geospatial_context=geospatial_context,
                ),
            },
        ]

        payload = {
            "model": self._settings.qwen_model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 320,
            "stream": True,
        }
        headers = {
            "Authorization": "Bearer " + self._settings.dashscope_api_key,
            "Content-Type": "application/json",
        }

        try:
            resp = self._session.post(
                url,
                headers=headers,
                json=payload,
                timeout=self._settings.request_timeout_seconds,
                stream=True,
            )
            self._raise_for_status(resp)

            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]  # strip "data: "
                if data_str.strip() == "[DONE]":
                    break
                import json as _json
                try:
                    chunk = _json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except _json.JSONDecodeError:
                    continue
        except (Timeout, RequestException) as exc:
            self._record_failure()
            raise UpstreamAPIError("Streaming failed") from exc

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
