#!/usr/bin/env python3
"""SightlineAI Demo Preparation Script.

Verifies dependencies, configuration, and server readiness before a demo.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


def check_python_version() -> bool:
    version = sys.version_info
    ok = version >= (3, 11)
    status = "✓" if ok else "✗"
    print(f"  {status} Python {version.major}.{version.minor}.{version.micro}")
    return ok


def check_dependencies() -> bool:
    required = ["fastapi", "uvicorn", "pydantic", "requests", "dotenv", "filetype"]
    ok = True
    for mod_name in required:
        try:
            importlib.import_module(mod_name)
            print(f"  ✓ {mod_name}")
        except ImportError:
            print(f"  ✗ {mod_name} — not installed")
            ok = False
    return ok


def check_env() -> bool:
    env_file = ROOT_DIR / ".env"
    has_env = env_file.exists()
    has_key = bool(os.getenv("DASHSCOPE_API_KEY"))

    status_env = "✓" if has_env else "⚠"
    status_key = "✓" if has_key else "⚠"

    print(f"  {status_env} .env file: {'found' if has_env else 'not found (use .env.example)'}")
    print(f"  {status_key} DASHSCOPE_API_KEY: {'configured' if has_key else 'not set (fallback mode only)'}")
    print(f"  ℹ  Fallback mode works without API key — demo will still be functional.")
    return True


def check_files() -> bool:
    critical = [
        "app/main.py", "app/config.py", "app/qwen_client.py",
        "app/schemas.py", "app/prompts.py", "app/utils.py",
        "frontend/index.html", "frontend/style.css", "frontend/app.js",
        "requirements.txt", ".env.example",
    ]
    ok = True
    for f in critical:
        exists = (ROOT_DIR / f).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {f}")
        if not exists:
            ok = False
    return ok


def check_config() -> bool:
    try:
        from app.config import get_settings
        s = get_settings()
        print(f"  ✓ Config loaded: {s.app_name} v{s.app_version}")
        print(f"  ✓ Model: {s.qwen_model}")
        print(f"  ✓ Image max: {s.image_max_bytes // 1024 // 1024} MB")
        print(f"  ✓ Timeout: {s.request_timeout_seconds}s")
        return True
    except Exception as exc:
        print(f"  ✗ Config error: {exc}")
        return False


def main() -> int:
    print("=" * 50)
    print("  SightlineAI Demo Preparation Checklist")
    print("=" * 50)

    checks = [
        ("Python version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration files", check_files),
        ("Environment", check_env),
        ("Config loading", check_config),
    ]

    results = []
    for name, fn in checks:
        print(f"\n[ {name} ]")
        results.append(fn())

    all_ok = all(results)

    print("\n" + "=" * 50)
    if all_ok:
        print("  ✓ ALL CHECKS PASSED — Ready to demo!")
    else:
        print("  ⚠ SOME CHECKS FAILED — Review above")
    print("=" * 50)

    print("\n📋 Demo startup command:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n📋 Then open: http://localhost:8000")
    print("\n📋 Demo guide: docs/demo-guide.md")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
