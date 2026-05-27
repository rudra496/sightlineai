# SightlineAI

SightlineAI is an accessibility-first AI assistant for blind and visually impaired users. It combines Qwen-powered guidance with deterministic fallback behavior so demos and real usage remain functional even in low-connectivity environments.

## What it solves

SightlineAI turns scene context into structured, safety-focused guidance:
- `guidance_text`: what to do next
- `safety_notes`: hazards to watch for
- `confidence_notes`: reliability caveats

## Core features

- Qwen-compatible guidance endpoint with strict request/response models
- Offline fallback guidance (automatic and manual)
- Image upload flow with safe type/size validation
- Voice-first frontend mode (speech recognition + speech synthesis)
- Geospatial context support with heuristic risk scoring
- Edge AI context endpoint for future on-device sensor fusion
- Session history APIs + local memory panel in frontend
- Public landing/docs page for judges and contributors

## What changed in this update

- Added new APIs: `/api/analyze-image`, `/api/edge-context`, `/api/fallback-guidance`, `/api/session-history`
- Implemented deterministic fallback pipeline and geospatial risk scoring
- Added image validation service and edge context abstraction layer
- Rebuilt frontend with image upload, voice controls, memory panel, and accessibility states
- Replaced landing page with product-style docs website sections
- Expanded docs: architecture, API, roadmap, usage, FAQ, security

## Architecture summary

Frontend (`/frontend`) → FastAPI backend (`app/main.py`) → Qwen client (`app/qwen_client.py`) OR fallback service (`app/services/fallback_guidance.py`) → structured output + history store.

See [docs/architecture.md](docs/architecture.md) for Mermaid flow.

## Setup

### Prerequisites

- Python 3.11+
- Optional DashScope API key for live Qwen responses

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment

```bash
cp .env.example .env
```

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DASHSCOPE_API_KEY` | Optional | — | Enables live Qwen guidance |
| `DASHSCOPE_BASE_URL` | No | DashScope compat URL | OpenAI-compatible base URL |
| `QWEN_MODEL` | No | `qwen3.7-max` | Qwen model name |
| `QWEN_TIMEOUT_SECONDS` | No | `25` | Upstream timeout |
| `MAX_IMAGE_BYTES` | No | `5242880` | Max image upload size |

## Run locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Interactive app UI: `http://localhost:8000`
- GitHub Pages landing/docs: repository root `index.html` (served on GitHub Pages)

## API endpoints

- `GET /api/health`
- `POST /api/guidance`
- `POST /api/fallback-guidance`
- `POST /api/analyze-image`
- `POST /api/edge-context`
- `GET /api/session-history`
- `POST /api/session-history`
- `DELETE /api/session-history`

Detailed payloads: [docs/api.md](docs/api.md)

## Workflows

### Image input workflow
1. Upload image in frontend.
2. Backend validates MIME/signature/size.
3. Fallback analysis returns structured guidance + image summary.

### Voice workflow
1. Browser speech recognition fills scene text (if supported).
2. User submits scene guidance.
3. Speech synthesis can read output aloud.

### Memory/history workflow
1. Every guidance response is stored in local browser history.
2. Backend also tracks in-memory session history.
3. Users can restore, pin, or clear recent responses.

### Fallback behavior
- `/api/guidance` automatically returns fallback output when Qwen is unavailable.
- `/api/fallback-guidance` forces deterministic fallback mode for demos.
- Fallback output is explicitly labeled (`mode: "fallback"`).

### Edge-AI-ready layer
- `/api/edge-context` accepts sensor-like payloads and returns risk score + actions.
- Service abstraction in `app/services/edge_context.py` is ready for future hardware adapters.

### Geospatial context
- Optional `geospatial_context` in guidance requests influences risk scoring.
- Heuristic scoring is intentionally conservative and documented as non-navigation-grade.

## Limitations

- Image pathway currently uses validated metadata + text hints (OCR not yet enabled).
- Session history store is in-memory and resets on backend restart.
- Geospatial scoring is heuristic, not map-verified navigation.
- Voice input depends on browser speech API availability.

## Security notes

- No hardcoded API keys.
- `.env` ignored via `.gitignore`.
- Bounded image uploads and strict schema validation.
- Structured request ID headers for error tracing.

See [docs/security.md](docs/security.md).

## Smoke checks

```bash
python scripts/smoke_test.py
python scripts/smoke_test.py --live
python scripts/self_check.py
```

## Demo links

- GitHub: https://github.com/rudra496/sightlineai
- Demo video: https://youtu.be/JQ796Gq9xMc

## Contributor notes

- Keep accessibility-first UX and structured output contracts stable.
- Add docs for every externally visible feature change.
