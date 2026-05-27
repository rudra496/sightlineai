# SightlineAI

SightlineAI is a hackathon-ready accessibility AI assistant for blind and visually impaired users, built for the **Global AI Hackathon Series with Qwen Cloud**.

It turns a short scene description into practical environmental guidance with safety-focused reasoning.

## Inspiration

Navigation in unfamiliar spaces can be risky without clear environmental context. SightlineAI demonstrates how Qwen-powered reasoning can provide concise guidance, obstacle awareness, and safer next actions.

## Features

- FastAPI backend with `POST /api/guidance`
- Qwen OpenAI-compatible integration via DashScope Model Studio
- Structured response output:
  - `guidance_text`
  - `safety_notes`
  - `confidence_notes`
- Robust error handling for missing API key, invalid input, timeout, network/API failures, and malformed responses
- Accessible, mobile-friendly frontend with optional text-to-speech
- Smoke test script for quick API client verification

## Architecture

See [docs/architecture.md](docs/architecture.md) for a Mermaid diagram and workflow.

## Qwen Integration

SightlineAI uses the OpenAI-compatible endpoint:

- Base URL (default): `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- Model (default): `qwen3.7-max`
- API key source: environment variable `DASHSCOPE_API_KEY`

No secrets are hardcoded.

## Local Setup

### 1) Prerequisites

- Python 3.11+

### 2) Install dependencies

```bash
cd /tmp/workspace/rudra496/sightlineai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure environment

```bash
cp .env.example .env
# Edit .env and set DASHSCOPE_API_KEY
```

Required variables:

- `DASHSCOPE_API_KEY` - your DashScope API key
- `DASHSCOPE_BASE_URL` - defaults to `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- `QWEN_MODEL` - defaults to `qwen3.7-max`

### 4) Run the app

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open: `http://localhost:8000`

## API Example

### Request

```bash
curl -X POST http://localhost:8000/api/guidance \
  -H "Content-Type: application/json" \
  -d '{"scene_description":"I am at a bus stop with a pole in front of me and traffic to my left."}'
```

### Example Response

```json
{
  "guidance_text": "Move half a step back, orient your body away from traffic, and keep your cane centered before moving forward slowly.",
  "safety_notes": "Obstacle directly ahead (pole) and moving vehicles on the left increase collision risk.",
  "confidence_notes": "Moderate confidence based on limited text context; verify with cane/contact points."
}
```

## Smoke Test

```bash
source .venv/bin/activate
python scripts/smoke_test.py
python scripts/smoke_test.py --live
```

- Without API key: script exits successfully and reports skip.
- With API key + `--live`: performs a real call and prints JSON.

## What Is Finished

- End-to-end local MVP (frontend + backend)
- Qwen integration with environment-based configuration
- Structured safety-focused guidance API
- Documentation and architecture diagram

## Future Work

- Camera input and multimodal scene analysis
- Edge-first sensor fusion pipeline
- Offline fallback guidance model
- Geospatial context integration for route safety

## Hackathon Context

This repository is prepared as a clean demo-ready MVP for the **Global AI Hackathon Series with Qwen Cloud**, focused on practical accessibility impact.

## License

MIT - see [LICENSE](LICENSE)
