from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8142"


def request_json(path: str, method: str = "GET", payload: dict | None = None, headers: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method, headers=request_headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def main() -> int:
    stderr_log = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix="-sightline-selfcheck.log")
    process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8142"],
        stdout=subprocess.DEVNULL,
        stderr=stderr_log,
    )

    try:
        time.sleep(2)

        checks: list[tuple[str, bool]] = []

        health_code, health = request_json("/api/health")
        checks.append(("health endpoint", health_code == 200 and health.get("status") == "ok"))

        guidance_code, guidance = request_json(
            "/api/guidance",
            method="POST",
            payload={"scene_description": "I hear traffic left and there are stairs ahead."},
        )
        checks.append(("guidance endpoint", guidance_code == 200 and "guidance_text" in guidance and "mode" in guidance))

        fallback_code, fallback = request_json(
            "/api/fallback-guidance",
            method="POST",
            payload={"scene_description": "Dark corridor with unknown obstacles"},
        )
        checks.append(("fallback endpoint", fallback_code == 200 and fallback.get("mode") == "fallback"))

        edge_code, edge = request_json(
            "/api/edge-context",
            method="POST",
            payload={"obstacle_distance_m": 0.8, "ambient_noise_db": 85, "motion_state": "walking"},
        )
        checks.append(("edge endpoint", edge_code == 200 and "risk_band" in edge))

        history_code, history = request_json("/api/session-history")
        checks.append(("session history endpoint", history_code == 200 and isinstance(history.get("items"), list)))

        fail_count = sum(0 if ok else 1 for _, ok in checks)
        for name, ok in checks:
            print(f"[self-check] {'PASS' if ok else 'FAIL'}: {name}")

        return 1 if fail_count else 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass
        stderr_log.close()
        if os.path.exists(stderr_log.name):
            os.unlink(stderr_log.name)


if __name__ == "__main__":
    raise SystemExit(main())
