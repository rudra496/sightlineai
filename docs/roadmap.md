# Roadmap

## ✅ Completed Features

### Core Guidance System
- [x] Qwen-powered AI guidance with structured JSON output
- [x] Automatic fallback on missing API key, timeout, or upstream failure
- [x] Deterministic offline guidance with hazard keyword detection
- [x] Retry logic with exponential backoff for transient failures
- [x] Circuit breaker pattern for Qwen client resilience

### Multimodal Input
- [x] Text-based scene description input
- [x] Image upload with MIME validation, magic-byte verification, and size limits
- [x] Voice input via Web Speech API (Chrome/Edge/Safari)
- [x] Text-to-speech output for guidance responses
- [x] Example scene chips for quick testing

### Context & Risk
- [x] Geospatial context support (location, route, hazards, time of day, mobility aid)
- [x] Heuristic risk scoring (0-100) with keyword-based adjustments
- [x] Edge AI context endpoint for future sensor fusion
- [x] Extended hazard keyword library (20+ categories)

### Memory & History
- [x] In-memory session history store (backend)
- [x] Local storage memory panel (frontend)
- [x] Pin/unpin guidance items
- [x] Restore previous sessions
- [x] Search history by source, keyword, and date range
- [x] Export all history as JSON
- [x] Delete individual or all history items

### Security & Architecture
- [x] Request ID tracing on all responses
- [x] Rate limiting (60 req/min per IP)
- [x] Request body size limits
- [x] Secure HTTP headers (CSP, X-Frame-Options, etc.)
- [x] Path traversal protection on static file serving
- [x] CORS hardening for production mode
- [x] Structured logging with request context
- [x] Graceful shutdown via lifespan handler
- [x] GZip response compression

### Frontend
- [x] Dark-first, accessibility-focused UI
- [x] Keyboard-only navigation support
- [x] Screen reader compatible (ARIA, semantic HTML)
- [x] Visible focus states and reduced-motion support
- [x] Toast notifications
- [x] Skeleton loading states
- [x] Image upload preview
- [x] Mode-aware badges (Qwen green / Fallback amber)
- [x] Risk score visualization bar
- [x] Mobile-responsive layout

### Documentation
- [x] Comprehensive README with badges and setup guide
- [x] API reference with curl examples
- [x] Architecture documentation with Mermaid diagrams
- [x] Security documentation
- [x] Usage guide
- [x] FAQ
- [x] Demo guide for judges
- [x] GitHub Pages landing page

### DevOps & Testing
- [x] Self-check script (automated endpoint validation)
- [x] Smoke test script (Qwen client verification)
- [x] Demo preparation script
- [x] Python syntax validation across all files
- [x] Health diagnostics endpoint

## 🔄 In Progress

### Image Analysis Enhancement
- [ ] Real OCR integration via pytesseract (optional dependency)
- [ ] Multimodal Qwen vision model integration for image understanding
- [ ] EXIF metadata extraction for orientation hints

## 📋 Planned

### Persistence & Scale
- [ ] SQLite or PostgreSQL-backed session history
- [ ] User authentication and multi-user support
- [ ] Session export to PDF/braille-ready formats

### Hardware Integration
- [ ] Bluetooth sensor adapter package (depth, LiDAR, IMU)
- [ ] Wearable device SDK hooks (smart glasses, haptic belts)
- [ ] ESP32/Camera module firmware for edge deployment
- [ ] Real-time sensor streaming via WebSocket

### Map & Navigation
- [ ] Map provider integration (OpenStreetMap, Google Maps)
- [ ] Real-time route safety scoring with live traffic data
- [ ] Indoor navigation support (beacon-based positioning)

### Advanced AI
- [ ] Multimodal Qwen vision model for real image understanding
- [ ] Continuous conversation context with memory window
- [ ] Personalized guidance based on user mobility profile
- [ ] Multi-language support (Bangla, Arabic, Spanish priority)

### Deployment
- [ ] Docker containerization
- [ ] Cloud deployment guide (Railway, Render, Fly.io)
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Automated accessibility testing (axe-core)

## Version History

| Version | Date | Highlights |
|---------|------|-----------|
| 0.2.0 | 2026-05 | Security hardening, enhanced fallback, memory search, docs overhaul |
| 0.1.0 | 2026-05 | Initial MVP: Qwen guidance, fallback, image, voice, geospatial |

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to help with roadmap items. Priority areas:
1. OCR integration (high impact, moderate effort)
2. Docker deployment (high impact, low effort)
3. Multi-language support (high impact, moderate effort)
