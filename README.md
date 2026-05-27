# SightlineAI

> **Qwen-powered environmental guidance for blind and visually impaired users.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Powered by Qwen](https://img.shields.io/badge/AI-Qwen%20via%20DashScope-ff6a00?logo=alibabadotcom&logoColor=white)](https://dashscope.console.aliyun.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

SightlineAI is a hackathon-ready accessibility AI assistant built for the **Global AI Hackathon Series with Qwen Cloud**. It turns a plain-language scene description into structured, safety-focused environmental guidance — helping blind and visually impaired users navigate their surroundings with greater confidence.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧭 **Structured guidance** | Three-part JSON response: `guidance_text`, `safety_notes`, `confidence_notes` |
| 🔊 **Text-to-speech** | Browser speech synthesis reads all guidance sections aloud |
| 📋 **Copy to clipboard** | One-click copy of complete guidance for sharing or logging |
| ⚡ **Example prompts** | Pre-loaded scene chips to demo the AI instantly |
| ♿ **Accessible UI** | Skip-link, ARIA live regions, focus rings, keyboard shortcut (`Ctrl`/`⌘`+`Enter`) |
| 📱 **Mobile responsive** | Scales cleanly from phone to desktop |
| 🛡️ **Robust error handling** | Graceful fallbacks for missing API key, timeout, network and parse failures |
| 🔑 **No hardcoded secrets** | API key read exclusively from environment variables |

---

## 🏗️ Architecture

```
User
 │  describes scene (text)
 ▼
Frontend (HTML/CSS/JS)
 │  POST /api/guidance
 ▼
FastAPI Backend
 │  validates input → builds prompt
 ▼
Qwen API (DashScope, OpenAI-compatible)
 │  returns structured JSON
 ▼
Frontend → displays cards + optional TTS
```

For the full Mermaid diagram and workflow walkthrough see [docs/architecture.md](docs/architecture.md).

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- A [DashScope API key](https://dashscope.console.aliyun.com/) (free tier available)

### 1 — Clone & install

```bash
git clone https://github.com/rudra496/sightlineai.git
cd sightlineai
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2 — Configure environment

```bash
cp .env.example .env
# Open .env and set DASHSCOPE_API_KEY to your key
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `DASHSCOPE_API_KEY` | ✅ yes | — | Your DashScope API key |
| `DASHSCOPE_BASE_URL` | no | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | OpenAI-compatible base URL |
| `QWEN_MODEL` | no | `qwen3.7-max` | Qwen model identifier |
| `QWEN_TIMEOUT_SECONDS` | no | `25` | Request timeout in seconds |

### 3 — Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in your browser.

---

## 🔌 API Reference

### `POST /api/guidance`

**Request**

```json
{
  "scene_description": "I am at a bus stop with a pole in front of me and traffic to my left."
}
```

Field constraints: `scene_description` must be 5–2000 characters.

**Response `200 OK`**

```json
{
  "guidance_text": "Step back half a pace to clear the pole, orient away from traffic, and use your cane to confirm the path forward before moving.",
  "safety_notes": "Obstacle directly ahead (pole) and moving traffic on your left — both increase collision risk.",
  "confidence_notes": "Moderate confidence from text context; verify with cane or tactile contact before each step."
}
```

**Error responses**

| Status | `error` field | Cause |
|---|---|---|
| 400 | `invalid_input` | Missing or too-short/long `scene_description` |
| 502 | `upstream_api_error` | Qwen API timeout or HTTP error |
| 503 | `configuration_error` | `DASHSCOPE_API_KEY` not set |
| 500 | `qwen_client_error` | Response parse failure |

### `GET /api/health`

```json
{ "status": "ok", "service": "SightlineAI", "model": "qwen3.7-max" }
```

---

## 🧪 Smoke Test

Verify the integration without running the full server:

```bash
# Checks config only (no API call)
python scripts/smoke_test.py

# Performs a real Qwen API call (requires DASHSCOPE_API_KEY)
python scripts/smoke_test.py --live

# Custom scene
python scripts/smoke_test.py --live --scene "I am on a narrow footbridge with railings on both sides."
```

---

## 📂 Project Structure

```
sightlineai/
├── app/
│   ├── config.py          # Settings loaded from environment variables
│   ├── main.py            # FastAPI app, routes, error handlers
│   ├── prompts.py         # Qwen system + user prompt builders
│   ├── qwen_client.py     # HTTP client with error classification
│   ├── schemas.py         # Pydantic request/response models
│   └── utils.py           # JSON extraction and response normalisation
├── frontend/
│   ├── index.html         # Accessible single-page UI
│   ├── style.css          # Dark-theme responsive styles
│   └── app.js             # Fetch, TTS, copy, example chips, char counter
├── docs/
│   └── architecture.md    # Mermaid diagram + workflow explanation
├── scripts/
│   └── smoke_test.py      # Offline/live integration smoke test
├── .env.example           # Environment variable template
└── requirements.txt       # Python dependencies
```

---

## 🗺️ Roadmap

- [ ] Camera / image input for multimodal scene analysis
- [ ] Edge AI layer — on-device sensor fusion for real-time guidance
- [ ] Offline fallback model for connectivity-limited environments
- [ ] Geospatial context integration for route safety scoring
- [ ] Conversation memory panel for session history
- [ ] Audio-first input mode (voice → scene description)

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 🔒 Security

No secrets are hardcoded. All credentials are loaded from environment variables via `python-dotenv`. See [SECURITY.md](SECURITY.md) for the vulnerability reporting process.

---

## 📄 License

[MIT](LICENSE) © 2024 SightlineAI Contributors

