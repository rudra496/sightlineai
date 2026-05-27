<p align="center">
  <img src="https://raw.githubusercontent.com/rudra496/sightlineai/main/frontend/favicon.svg" alt="SightlineAI Logo" width="80" height="80">
</p>

<h1 align="center">SightlineAI</h1>

<p align="center"><strong>Accessibility-First AI Guidance for Blind & Visually Impaired Users</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-0.111+-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Qwen_AI-Powered-FF6B6B.svg" alt="Qwen AI Powered">
  <img src="https://img.shields.io/badge/Multi-Language-4_Langs-73e2ab.svg" alt="Multi-Language">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white" alt="Docker Ready">
  <img src="https://img.shields.io/github/stars/rudra496/sightlineai?style=social" alt="GitHub Stars">
  <img src="https://img.shields.io/github/forks/rudra496/sightlineai?style=social" alt="GitHub Forks">
</p>

<p align="center">
  <a href="https://github.com/rudra496/sightlineai">GitHub</a> ·
  <a href="https://rudra496.github.io/sightlineai">Live Demo</a> ·
  <a href="https://youtu.be/JQ796Gq9xMc">Demo Video</a> ·
  <a href="docs/api.md">API Docs</a> ·
  <a href="docs/architecture.md">Architecture</a>
</p>

---

> **SightlineAI** turns environmental context into structured, safety-focused guidance for blind and visually impaired users — powered by **Qwen AI** with deterministic offline fallback, multi-language support, real-time vision analysis, WebSocket streaming, and conversation memory. It **always works**, even without connectivity.

---

## 💔 The Problem

Over **2.2 billion people** worldwide live with vision impairment, yet most navigation tools require stable internet, expensive hardware, or both. When connectivity drops — in rural areas, underground transit, or during emergencies — these tools silently fail the people who need them most.

**SightlineAI exists to close that gap.**

---

## ✨ Features

### 🧠 AI-Powered Guidance
| Feature | Description |
|---|---|
| **Qwen AI Engine** | Structured responses with action steps, safety notes, and confidence ratings |
| **Vision Analysis** | Real image understanding via Qwen multimodal vision API |
| **Conversation Mode** | Multi-turn dialogue with context memory across messages |
| **WebSocket Streaming** | Real-time token-by-token response streaming |
| **Offline Fallback** | Deterministic guidance engine that works without network or API key |

### 🌍 Multi-Language & Accessibility
| Feature | Description |
|---|---|
| **4 Languages** | English, Bangla (বাংলা), Arabic (العربية), Spanish (Español) |
| **Voice Input/Output** | Speech recognition + synthesis for hands-free, eyes-free interaction |
| **ARIA Labels** | Full screen reader support with semantic HTML |
| **Keyboard Navigation** | Complete keyboard-only operation |

### 📊 Advanced Features
| Feature | Description |
|---|---|
| **Geospatial Risk Scoring** | Heuristic risk assessment from location, route, and hazard context |
| **Edge AI Context** | Sensor-fusion risk scoring endpoint for future hardware integration |
| **Accessibility Scoring** | Obstacle density, path clarity, and sensory cue analysis |
| **Session Memory** | Persistent history with pin, favorite, search, and export (JSON/CSV/Markdown) |
| **Runtime Settings** | Change model and timeout without restart via API |
| **SQLite Persistence** | Optional database-backed storage for production deployments |

### 🔒 Security & Reliability
- Circuit breaker pattern with exponential backoff
- Rate limiting (60 req/min per IP)
- CSP headers, input validation, bounded uploads
- Request ID tracing on all responses
- GZip compression

---

## 🚀 Quick Start

### Option 1: Direct Install
```bash
git clone https://github.com/rudra496/sightlineai.git
cd sightlineai
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your DashScope API key (optional)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Docker
```bash
git clone https://github.com/rudra496/sightlineai.git
cd sightlineai
cp .env.example .env  # Add your API key
docker-compose up -d
```

Open **http://localhost:8000** — works immediately with offline fallback (no API key required).

---

## 📡 API Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health, uptime, version |
| `POST` | `/api/guidance` | AI guidance with automatic fallback |
| `POST` | `/api/fallback-guidance` | Force deterministic offline guidance |
| `POST` | `/api/analyze-image` | Image upload → AI vision analysis |
| `POST` | `/api/edge-context` | Sensor-fusion risk scoring |
| `POST` | `/api/conversation` | Multi-turn conversation with context |
| `GET` | `/api/conversation/{id}` | Get conversation history |
| `DELETE` | `/api/conversation/{id}` | Delete conversation |
| `POST` | `/api/accessibility-score` | Scene accessibility analysis |
| `GET` | `/api/settings` | View runtime configuration |
| `POST` | `/api/settings` | Update runtime settings |
| `WS` | `/ws/guidance` | WebSocket streaming guidance |
| `GET` | `/api/session-history` | List session history |
| `POST` | `/api/session-history/search` | Search history by source/keyword/date |
| `POST` | `/api/session-history/pin` | Pin a history item |
| `POST` | `/api/session-history/favorite` | Favorite a history item |
| `GET` | `/api/session-history/favorites` | List favorites |
| `GET` | `/api/session-history/export` | Export as JSON |
| `GET` | `/api/session-history/export/csv` | Export as CSV |
| `GET` | `/api/session-history/export/markdown` | Export as Markdown |
| `GET` | `/api/offline-status` | Offline capability status |

📖 **Full API reference:** [docs/api.md](docs/api.md)

---

## 🏗️ Architecture

```
User → Frontend (Text/Voice/Image/Memory) → FastAPI API
  → Validation (Pydantic v2)
  → Qwen Client (cloud AI with circuit breaker) ──or── Fallback Service (deterministic)
  → Geospatial Risk Scoring → Session History Store → Structured Response
  → Optional: WebSocket streaming, Conversation context, SQLite persistence
```

📖 **Full architecture:** [docs/architecture.md](docs/architecture.md)

---

## 🛠️ Tech Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, Uvicorn
- **AI:** Qwen 3.7 (via DashScope OpenAI-compatible API), multimodal vision
- **Frontend:** Vanilla HTML/CSS/JS (zero dependencies)
- **Voice:** Web Speech API (recognition + synthesis)
- **Persistence:** In-memory (default) or SQLite (opt-in)
- **Streaming:** WebSocket with token-by-token delivery
- **Security:** Rate limiting, CSP headers, input validation, circuit breaker
- **Deployment:** Docker, docker-compose

---

## 🌐 Multi-Language Support

SightlineAI supports guidance in 4 languages:

| Language | Code | Status |
|---|---|---|
| English | `en` | ✅ Full support |
| Bangla (বাংলা) | `bn` | ✅ AI + Bangla fallback templates |
| Arabic (العربية) | `ar` | ✅ AI-powered |
| Spanish (Español) | `es` | ✅ AI-powered |

Set language via the UI dropdown or API `language` parameter.

---

## ♿ Accessibility Philosophy

SightlineAI is built **accessibility-first**, not as an afterthought:

- **Voice-first interaction** — hands-free, eyes-free via speech
- **Structured output** — every response separates actions, safety, and confidence
- **Offline resilience** — deterministic fallback ensures guidance never disappears
- **Conservative defaults** — risk scoring errs on the side of caution
- **Standards compliance** — ARIA labels, keyboard nav, reduced-motion support
- **Multi-language** — serving users in their native language

Every design decision asks: *"Does this work for someone who can't see the screen?"*

---

## 🗺️ Roadmap

- [x] Qwen-powered AI guidance with structured JSON output
- [x] Automatic fallback on missing API key, timeout, or upstream failure
- [x] Deterministic offline guidance with hazard keyword detection
- [x] Image upload with Qwen vision model analysis
- [x] Voice input via Web Speech API + text-to-speech output
- [x] Multi-language support (EN, BN, AR, ES)
- [x] Continuous conversation with context memory
- [x] WebSocket streaming for real-time responses
- [x] Session history with pin, favorite, search, and export
- [x] Accessibility score endpoint (obstacle density, path clarity, sensory cues)
- [x] Runtime settings API
- [x] SQLite persistent storage
- [x] Docker containerization
- [ ] OCR extraction (pytesseract integration)
- [ ] Map provider integration (OpenStreetMap)
- [ ] Hardware sensor adapter (LiDAR, IMU)
- [ ] User authentication and multi-user support

📖 **Detailed roadmap:** [docs/roadmap.md](docs/roadmap.md)

---

## 🏆 Awards & Recognition

- 🥇 **DEI Champion** — Rice360, Rice University (2025)
- 🏆 **Divisional Champion** — ICT Division, Bangladesh (2025)
- 🏆 **Champion (Cohort-5)** — University Innovation Hub Program (2025)
- 🥉 **2nd Runner's Up** — VisionX Program, University of Dhaka (2025)
- 🎓 **Lean Six Sigma White Belt** (2025)
- **Pre-seed funded** startup

---

## 🤝 Contributing

Contributions are welcome! Read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- Keep accessibility-first UX and structured output contracts stable
- Add docs for every externally visible feature change
- Write clear commit messages and focused PRs

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 📬 Contact

<p align="left">
  <a href="https://github.com/rudra496">GitHub</a> ·
  <a href="https://rudra496.github.io/site">Portfolio</a> ·
  <a href="https://www.linkedin.com/in/rudrasarker">LinkedIn</a> ·
  <a href="mailto:rudrasarker130@gmail.com">Email</a> ·
  <a href="https://x.com/Rudra496">Twitter/X</a>
</p>

**Rudra Sarker** — 3rd-year IPE Student, SUST · Founder of SightlineAI & MindWell · Open Source Advocate

---

## 🙏 Acknowledgments

- **Rice360 Institute for Global Health Technologies** — DEI Award
- **University Innovation Hub Program (UIHP)** — Champion Award
- **Shahjalal University of Science and Technology (SUST)** — Academic Support
- Built with ❤️ for the global accessibility community

---

> ⭐ **If this project helps you, please consider giving it a star!** It helps others discover SightlineAI.
