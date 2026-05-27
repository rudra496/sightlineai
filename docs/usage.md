# Usage Guide

## Quick Start

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment (optional)

```bash
cp .env.example .env
# Edit .env to add your DashScope API key (optional)
```

### 3. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in your browser.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DASHSCOPE_API_KEY` | No | — | DashScope API key for live Qwen guidance |
| `DASHSCOPE_BASE_URL` | No | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | OpenAI-compatible base URL |
| `QWEN_MODEL` | No | `qwen3.7-max` | Qwen model name |
| `QWEN_TIMEOUT_SECONDS` | No | `25` | Upstream API timeout in seconds |
| `MAX_IMAGE_BYTES` | No | `5242880` (5 MB) | Maximum image upload size |
| `PRODUCTION` | No | `false` | Enable production CORS restrictions |

## Workflows

### Text Guidance
1. Enter a scene description in the text area (minimum 5 characters).
2. Optionally add location, route notes, and known hazards.
3. Click **"Analyze scene"** or press `Ctrl+Enter` (`⌘+Enter` on Mac).
4. Read the structured response: guidance, safety notes, confidence notes.

### Image Analysis
1. Click the file input and select a JPG, PNG, or WebP image (max 5 MB).
2. Optionally add a text hint describing what's in the image.
3. Click **"Analyze image"**.
4. The backend validates the image, analyzes it, and returns structured guidance.

### Voice Input
1. Click the **"Voice input"** button (requires Chrome, Edge, or Safari).
2. Speak your scene description naturally.
3. The transcript appears in the scene description field.
4. Submit normally.

### Text-to-Speech
1. After receiving guidance, click **"Speak guidance"**.
2. The browser reads the guidance, safety notes, and confidence notes aloud.
3. Works in all modern browsers.

### Offline / Fallback Mode
1. Click **"Force offline fallback"** to test deterministic guidance.
2. Or simply run without a `DASHSCOPE_API_KEY` — fallback activates automatically.
3. The response will show `mode: "fallback"` with risk assessment.

### Session Memory
1. All guidance responses are automatically saved to session memory.
2. Click **"Pin to memory"** to pin the latest guidance.
3. Click **"Restore"** on any history item to reload it.
4. Click **"Clear"** to erase all local history.

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Enter` / `⌘+Enter` | Submit scene analysis |
| `Tab` / `Shift+Tab` | Navigate between elements |
| `Enter` / `Space` | Activate focused button or chip |
| `Escape` | Stop voice recording |

## Troubleshooting

### "Voice unavailable" button
Your browser doesn't support the Web Speech API. Use Chrome, Edge, or Safari, or type your scene description manually.

### Guidance always shows "fallback" mode
The `DASHSCOPE_API_KEY` is either not set or invalid. Check your `.env` file. Fallback mode still provides useful deterministic guidance.

### Image upload fails with "Unsupported image type"
Ensure your image is JPG, PNG, or WebP. The backend checks both the file extension and the actual file signature.

### Port 8000 already in use
Use a different port: `uvicorn app.main:app --port 8001`

### Import errors
Ensure your virtual environment is activated and all dependencies are installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

### Self-check (automated endpoint validation)
```bash
python scripts/self_check.py
```

### Smoke test (Qwen client verification)
```bash
# Without API key (config check only)
python scripts/smoke_test.py

# With API key (live test)
python scripts/smoke_test.py --live
```

### Demo preparation
```bash
python scripts/demo_prep.py
```

## API Quick Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Service health and diagnostics |
| GET | `/api/offline-status` | Offline capability status |
| POST | `/api/guidance` | AI guidance with auto-fallback |
| POST | `/api/fallback-guidance` | Force deterministic fallback |
| POST | `/api/analyze-image` | Image upload analysis |
| POST | `/api/edge-context` | Edge sensor context scoring |
| GET | `/api/session-history` | List all history items |
| POST | `/api/session-history` | Create manual history item |
| POST | `/api/session-history/search` | Search history |
| POST | `/api/session-history/pin` | Pin an item |
| POST | `/api/session-history/unpin` | Unpin an item |
| GET | `/api/session-history/export` | Export all history as JSON |
| DELETE | `/api/session-history/{id}` | Delete a specific item |
| DELETE | `/api/session-history` | Clear all history |
