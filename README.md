<div align="center">

# 👁️ SightlineAI

### AI-Powered Accessibility Guidance Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Open Source](https://img.shields.io/badge/Open%20Source-❤️-red.svg)](https://opensource.org)

**Real-time AI guidance for the visually impaired — scene analysis, obstacle detection, OCR, and multi-language navigation at 94% less cost.**

[🌐 Live Demo](https://rudra496.github.io/sightlineai) · [📖 Documentation](#api-reference) · [🐛 Report Bug](https://github.com/rudra496/sightlineai/issues) · [💡 Request Feature](https://github.com/rudra496/sightlineai/issues)

</div>

---

## 🌟 Vision

> **"Making the world navigable for everyone, one step at a time."**

285 million people worldwide live with visual impairment. 90% are in developing countries where assistive technology costs $3,000–$5,000 — completely out of reach. SightlineAI changes this: a full-featured AI accessibility platform at **$199 per device**, that's a **94% cost reduction**.

## 🔍 Problem & Market

| Metric | Value |
|--------|-------|
| Global visually impaired population | 285 million |
| Unmet need in developing nations | 80%+ |
| Average assistive device cost | $3,500 |
| SightlineAI device cost | $199 |
| Global assistive tech market (TAM) | $28B |
| AI accessibility segment (SAM) | $4.2B |
| South Asia + Middle East (SOM) | $620M |

## ✨ Solution Overview

SightlineAI is a full-stack AI platform that transforms any camera-equipped device into an intelligent accessibility companion:

1. **📷 Capture** — Camera + hardware sensors (LiDAR/IMU) capture the environment
2. **🧠 Analyze** — Qwen AI processes scenes, text (OCR), objects, and hazards
3. **⚖️ Assess** — Risk engine evaluates danger levels and accessibility scores
4. **🗣️ Guide** — Multi-language voice/text guidance via real-time WebSocket streaming

## 🚀 Features

### AI Engine
| Feature | Description |
|---------|-------------|
| 🧠 **Qwen AI Integration** | State-of-the-art Qwen 2.5 model for scene understanding |
| 👁️ **Vision Analysis** | Real-time object detection and spatial understanding |
| 💬 **Conversation Mode** | Multi-turn dialogue with conversation memory |
| 🔄 **Offline Fallback** | Cached responses and local processing offline |

### Input Processing
| Feature | Description |
|---------|-------------|
| 📷 **Camera Capture** | Real-time frame capture optimized for varied conditions |
| 📄 **OCR Engine** | Read signs, labels, documents with high accuracy |
| 📡 **Sensor Fusion** | LiDAR/IMU integration for obstacle detection |
| 🎤 **Voice Input** | Hands-free voice commands with noise cancellation |

### Context & Navigation
| Feature | Description |
|---------|-------------|
| 🗺️ **OpenStreetMap** | Location context, POI discovery, accessibility routing |
| ⚠️ **Risk Engine** | Dynamic danger evaluation with severity scoring |
| 📊 **Accessibility Scoring** | Quantitative accessibility metrics for routes/locations |
| 🧭 **Navigation Guidance** | Step-by-step voice navigation with obstacle avoidance |

### Platform
| Feature | Description |
|---------|-------------|
| 🌐 **Multi-Language** | English, Bangla, Arabic, Spanish with auto-detection |
| ⚡ **WebSocket Streaming** | Real-time bidirectional streaming for instant responses |
| 🔐 **Authentication** | JWT-based user accounts with session management |
| ⭐ **Favorites & Memory** | Save locations, conversations, and user preferences |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SightlineAI Pipeline                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐     ┌──────────┐     ┌──────────────────────────┐ │
│  │ 👤 User   │────▶│ 🖥️ Web   │────▶│ 🚀 API Gateway (FastAPI) │ │
│  │  Input    │     │  Client  │     │  + JWT Auth + Routing   │ │
│  │ Voice/    │     │ React +  │     └────────────┬─────────────┘ │
│  │ Camera/   │     │ WebSocket│                  │               │
│  │ Sensors   │     └──────────┘                  ▼               │
│  └──────────┘                         ┌────────────────────┐    │
│                                       │  AI Processing Hub │    │
│                                       │ ┌──────┐ ┌──────┐ │    │
│                                       │ │Qwen  │ │Vision│ │    │
│                                       │ │ AI   │ │Module│ │    │
│                                       │ ├──────┤ ├──────┤ │    │
│                                       │ │OCR   │ │Sensor│ │    │
│                                       │ │Engine│ │Fusion│ │    │
│                                       │ └──────┘ └──────┘ │    │
│                                       └────────┬───────────┘    │
│                                                │                 │
│                                                ▼                 │
│                                       ┌────────────────────┐    │
│                                       │ ⚠️ Risk Engine     │    │
│                                       │ Danger Assessment   │    │
│                                       │ Accessibility Score │    │
│                                       └────────┬───────────┘    │
│                                                │                 │
│                                                ▼                 │
│                                       ┌────────────────────┐    │
│                                       │ 💾 Memory Store    │    │
│                                       │ Conversations +    │    │
│                                       │ Favorites + Prefs  │    │
│                                       └────────┬───────────┘    │
│                                                │                 │
│                                                ▼                 │
│                                       ┌────────────────────┐    │
│                                       │ 🗣️ Response Layer  │    │
│                                       │ Multi-Language EN/ │    │
│                                       │ BN/AR/ES + Stream  │    │
│                                       └────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 📡 API Reference

### Core AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze/scene` | Analyze scene from camera frame |
| `POST` | `/api/v1/analyze/image` | Analyze uploaded image |
| `POST` | `/api/v1/ocr/extract` | Extract text from image |
| `POST` | `/api/v1/ocr/document` | Process full document |
| `WS` | `/api/v1/chat/stream` | WebSocket conversation streaming |
| `POST` | `/api/v1/chat/message` | Send single chat message |
| `GET` | `/api/v1/chat/history/{id}` | Get conversation history |
| `DELETE` | `/api/v1/chat/history/{id}` | Delete conversation |
| `POST` | `/api/v1/vision/describe` | Describe visual scene |
| `POST` | `/api/v1/vision/detect` | Detect objects in frame |

### Navigation & Context
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/nav/route` | Get accessible route |
| `GET` | `/api/v1/nav/poi` | Nearby points of interest |
| `GET` | `/api/v1/nav/geocode` | Reverse geocode location |
| `POST` | `/api/v1/risk/assess` | Assess risk from scene data |
| `GET` | `/api/v1/accessibility/score` | Get accessibility score |

### Sensor & Hardware
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/sensors/lidar` | Process LiDAR scan data |
| `POST` | `/api/v1/sensors/imu` | Process IMU sensor data |
| `POST` | `/api/v1/sensors/fusion` | Multi-sensor fusion processing |

### User Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | Login and get JWT |
| `POST` | `/api/v1/auth/refresh` | Refresh JWT token |
| `GET` | `/api/v1/users/me` | Get current user profile |
| `PUT` | `/api/v1/users/me` | Update user profile |
| `GET` | `/api/v1/users/preferences` | Get user preferences |
| `PUT` | `/api/v1/users/preferences` | Update preferences |

### Favorites
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/favorites` | List user favorites |
| `POST` | `/api/v1/favorites` | Add a favorite |
| `DELETE` | `/api/v1/favorites/{id}` | Remove a favorite |
| `GET` | `/api/v1/favorites/{id}` | Get favorite details |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/system/status` | System status |
| `GET` | `/api/v1/languages` | List supported languages |
| `GET` | `/api/v1/config/offline` | Get offline fallback config |

## ⚡ Quick Start

### Using pip

```bash
# Clone the repository
git clone https://github.com/rudra496/sightlineai.git
cd sightlineai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the server
python -m app.main
```

### Using Docker

```bash
# Clone and run with Docker Compose
git clone https://github.com/rudra496/sightlineai.git
cd sightlineai

# Start all services
docker compose up -d

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## ⚙️ Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `QWEN_API_KEY` | Qwen AI API key | — | ✅ |
| `QWEN_MODEL` | Qwen model name | `qwen2.5` | ❌ |
| `SECRET_KEY` | JWT signing key | — | ✅ |
| `DATABASE_URL` | Database connection string | `sqlite:///./sightline.db` | ❌ |
| `REDIS_URL` | Redis for caching/sessions | `redis://localhost:6379` | ❌ |
| `OFFLINE_MODE` | Enable offline fallback | `false` | ❌ |
| `DEFAULT_LANGUAGE` | Default language code | `en` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |
| `CORS_ORIGINS` | Allowed CORS origins | `*` | ❌ |
| `WEBSOCKET_HEARTBEAT` | WebSocket heartbeat interval (s) | `30` | ❌ |
| `MAX_IMAGE_SIZE` | Max upload image size (MB) | `10` | ❌ |
| `OSM_ENDPOINT` | OpenStreetMap Overpass endpoint | `https://overpass-api.de/api` | ❌ |

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.11+ | Core backend language |
| **FastAPI** | 0.104+ | Async API framework |
| **Qwen AI** | 2.5 | Language/vision model |
| **WebSocket** | — | Real-time streaming |
| **React** | 18+ | Frontend framework |
| **Docker** | Compose | Containerization |
| **OpenStreetMap** | Overpass API | Maps & geolocation |
| **SQLite/PostgreSQL** | — | Data persistence |
| **Redis** | 7+ | Caching & sessions |
| **JWT** | — | Authentication |
| **LiDAR/IMU** | — | Hardware sensor adapter |

## 🌐 Multi-Language Support

| Language | Code | Status | Script |
|----------|------|--------|--------|
| 🇬🇧 English | `en` | ✅ Complete | Latin |
| 🇧🇩 Bangla | `bn` | ✅ Complete | Bengali |
| 🇸🇦 Arabic | `ar` | ✅ Complete | Arabic (RTL) |
| 🇪🇸 Spanish | `es` | ✅ Complete | Latin |

All languages support voice output, text display, and OCR with automatic language detection.

## 💼 Business Model

### Revenue Streams

| Channel | Model | Pricing |
|---------|-------|---------|
| 🏥 **B2B** — Hospitals, Clinics, Rehabilitation Centers | Device + License | $199/device |
| 🏛️ **B2G** — Government Accessibility Programs | Volume Licensing | Custom |
| 👤 **B2C** — Individual Users | Freemium | Free / Premium |
| 🤝 **NGO Partnerships** — BRAC, WHO, Sightsavers | Sponsored Distribution | Grant-funded |

### Competitive Advantage

| | Traditional Devices | SightlineAI |
|---|---|---|
| **Cost** | $3,000 – $5,000 | **$199** |
| **AI-Powered** | Limited | ✅ Full Qwen AI |
| **Offline Mode** | Rare | ✅ Built-in |
| **Multi-Language** | Usually 1-2 | ✅ 4 Languages |
| **Open Source** | ❌ | ✅ MIT License |
| **Real-time Streaming** | ❌ | ✅ WebSocket |

### Target Partners
BRAC · Bangladesh Eye Hospital · icddr,b · WHO · Sightsavers · CBM International

## 🌱 Impact & SDGs

SightlineAI aligns with the United Nations Sustainable Development Goals:

- 💚 **SDG 3** — Good Health & Well-being: Improving quality of life for visually impaired individuals
- ❤️ **SDG 10** — Reduced Inequalities: Making assistive technology affordable and accessible
- 💛 **SDG 11** — Sustainable Cities: Enabling safe navigation in urban environments

**Projected Impact (Year 1):**
- 🎯 10,000+ active users
- 💰 94% cost reduction vs. alternatives
- 🌍 4 language communities served
- 📖 100% open source and transparent

## 🏆 Awards & Recognition

| Award | Year | Organization |
|-------|------|-------------|
| 🥇 **Rice360 DEI Champion** | 2024 | Rice University |
| 🥇 **ICT Division Champion** | 2024 | Bangladesh ICT Division |
| 🥇 **UIHP Champion** | 2024 | University Innovation Hub Program |
| 🏅 **VisionX Finalist** | 2024 | VisionX Competition |

**Funding:** Pre-seed funded

## 🗺️ Roadmap

- [x] ~~Core Qwen AI integration with scene analysis~~
- [x] ~~WebSocket real-time streaming~~
- [x] ~~Multi-language support (EN, BN, AR, ES)~~
- [x] ~~Offline fallback mode~~
- [x] ~~OCR text extraction engine~~
- [x] ~~Vision analysis module~~
- [x] ~~Conversation mode with memory~~
- [x] ~~Risk assessment engine~~
- [x] ~~Accessibility scoring system~~
- [x] ~~OpenStreetMap integration~~
- [x] ~~Hardware sensor adapter (LiDAR/IMU)~~
- [x] ~~User authentication (JWT)~~
- [x] ~~Favorites and preferences~~
- [x] ~~Docker containerization~~
- [x] ~~REST API (25+ endpoints)~~
- [x] ~~Responsive web frontend~~
- [x] ~~Comprehensive documentation~~

## 🤝 Contributing

We welcome contributions from everyone! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Ways to Contribute
- 🐛 Bug reports and fixes
- 🌐 Translation improvements
- ♿ Accessibility enhancements
- 📖 Documentation updates
- 🧪 Test coverage
- 🎨 UI/UX improvements

Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License — Free for personal and commercial use.
```

## 📬 Contact

**Rudra Sarker** — Founder & Lead Developer

| Platform | Link |
|----------|------|
| 📧 Email | [rudrasarker130@gmail.com](mailto:rudrasarker130@gmail.com) |
| 🐙 GitHub | [rudra496](https://github.com/rudra496) |
| 💼 LinkedIn | [rudrasarker](https://www.linkedin.com/in/rudrasarker) |
| 🐦 Twitter/X | [@Rudra496](https://x.com/Rudra496) |
| 🌐 Portfolio | [rudra496.github.io/site](https://rudra496.github.io/site) |
| 🎓 University | [SUST](https://www.sust.edu), Sylhet, Bangladesh |

Project Link: [https://github.com/rudra496/sightlineai](https://github.com/rudra496/sightlineai)

## 🙏 Acknowledgments

- **Qwen AI Team** for the powerful language model
- **OpenStreetMap** contributors worldwide
- **Rice University** Rice360 Institute for Global Health Technologies
- **Bangladesh ICT Division** for supporting innovation
- **SUST** — Shahjalal University of Science and Technology
- The global **accessibility community** for inspiration and feedback
- Every **open source contributor** who makes technology more inclusive

---

<div align="center">

**Built with ❤️ for accessibility**

[⬆ Back to Top](#-sightlineai)

</div>

## Connect

- [![GitHub](https://img.shields.io/badge/GitHub-rudra496-181717?logo=github)](https://github.com/rudra496)
- [![LinkedIn](https://img.shields.io/badge/LinkedIn-rudrasarker-0A66C2?logo=linkedin)](https://www.linkedin.com/in/rudrasarker)
- [![X/Twitter](https://img.shields.io/badge/X-@Rudra496-000000?logo=x)](https://x.com/Rudra496)
- [![YouTube](https://img.shields.io/badge/YouTube-@rudrasarker9732-FF0000?logo=youtube)](https://youtube.com/@rudrasarker9732)
- [![Dev.to](https://img.shields.io/badge/Dev.to-rudra__sarker-000000?logo=devdotto)](https://dev.to/rudra_sarker)
