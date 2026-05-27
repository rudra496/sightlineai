from __future__ import annotations

import argparse
import json
import sys

from app.config import get_settings
from app.qwen_client import MissingAPIKeyError, QwenClient, UpstreamAPIError



def run_smoke(scene: str, allow_live_call: bool) -> int:
    settings = get_settings()
    client = QwenClient(settings)

    print("[smoke] Config loaded")
    print(f"[smoke] Base URL: {settings.dashscope_base_url}")
    print(f"[smoke] Model: {settings.qwen_model}")

    if not client.has_api_key:
        print("[smoke] DASHSCOPE_API_KEY not set. Skipping live API call.")
        return 0

    if not allow_live_call:
        print("[smoke] API key detected. Re-run with --live to perform a real API check.")
        return 0

    try:
        result = client.get_guidance(scene)
    except MissingAPIKeyError as exc:
        print(f"[smoke] FAILED: {exc}")
        return 1
    except UpstreamAPIError as exc:
        print(f"[smoke] FAILED: {exc}")
        return 1

    print("[smoke] SUCCESS")
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SightlineAI Qwen client smoke test")
    parser.add_argument(
        "--scene",
        default="I am near a narrow sidewalk with a trash can ahead and stairs to the right.",
        help="Scene description to send to Qwen",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run a live Qwen API request when DASHSCOPE_API_KEY is present",
    )
    args = parser.parse_args()
    sys.exit(run_smoke(args.scene, args.live))
