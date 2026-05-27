# Frequently Asked Questions

## General

### What is SightlineAI?
SightlineAI is an accessibility-first AI assistant designed to help blind and visually impaired users navigate their environment. It provides structured safety guidance through text, voice, and image inputs — with resilient offline fallback when cloud AI is unavailable.

### Who is it for?
Primarily blind and visually impaired individuals, but also useful for anyone who needs environmental awareness guidance — elderly users, people with cognitive disabilities, or first responders in unfamiliar environments.

### Is it a certified navigation system?
No. SightlineAI provides **guidance and safety suggestions**, not certified navigation. Users should always verify surroundings with their preferred mobility aid (cane, guide dog, etc.).

## Technical

### What AI model does it use?
SightlineAI uses **Qwen** (Alibaba's large language model) via the DashScope API with an OpenAI-compatible endpoint. When Qwen is unavailable, it falls back to deterministic rule-based guidance.

### Does it work without internet?
Yes. The deterministic fallback system generates safety guidance using rule-based hazard detection, keyword analysis, and geospatial heuristics. No cloud API is needed for fallback mode.

### What programming language / framework?
- **Backend:** Python 3.11+ with FastAPI
- **Frontend:** Vanilla HTML/CSS/JavaScript (no build step)
- **AI:** Qwen via DashScope OpenAI-compatible API

### How do I get a DashScope API key?
Visit [DashScope International](https://dashscope-intl.aliyuncs.com/) to register. The API key is optional — SightlineAI works in fallback mode without it.

### What image formats are supported?
JPEG, PNG, and WebP. Maximum file size is 5 MB. The backend validates both the file extension and the actual file signature (magic bytes).

### Is there a mobile app?
Not yet. The web frontend is mobile-responsive and works in mobile browsers. Voice input uses the Web Speech API (available in Chrome, Edge, and Safari).

## Accessibility

### How does voice input work?
SightlineAI uses the browser's built-in Web Speech API for speech recognition. This works in Chrome, Edge, and Safari. Firefox and some mobile browsers may not support it — in that case, text input is always available.

### How does text-to-speech work?
The "Speak guidance" button uses the browser's `speechSynthesis` API to read the guidance, safety notes, and confidence notes aloud. This works in all modern browsers.

### Can I navigate with just a keyboard?
Yes. All interactive elements are keyboard-accessible:
- `Tab` / `Shift+Tab` to navigate
- `Enter` or `Space` to activate buttons and chips
- `Ctrl+Enter` (or `⌘+Enter`) to submit scene analysis
- `Escape` to stop voice recording
- A "Skip to content" link appears on focus

### Does it support screen readers?
Yes. The frontend uses semantic HTML, ARIA labels, live regions, and proper heading hierarchy. Status updates are announced via `aria-live` regions.

### What about users who prefer reduced motion?
All animations respect the `prefers-reduced-motion` media query. When enabled, transitions and animations are disabled.

## Security & Privacy

### Are my images stored on the server?
No. Images are processed in-memory during the request and never written to disk. No persistent storage of uploaded images occurs.

### Are API keys exposed in the frontend?
No. The DashScope API key is only used server-side. The frontend communicates only with the local FastAPI backend.

### Can I self-host SightlineAI?
Yes. Clone the repository, install dependencies, optionally set your DashScope API key, and run the server. Everything runs locally.

## Hackathon / Demo

### How do I demo SightlineAI to judges?
See our [Demo Guide](demo-guide.md) for a step-by-step 2-minute demo script.

### What if the internet is unreliable during the demo?
Use the "Force offline fallback" button — it demonstrates the deterministic fallback mode which requires no internet connection.

### Can I use it without a DashScope API key?
Absolutely. Without an API key, SightlineAI operates in fallback mode with full functionality. The guidance is rule-based rather than AI-generated, but still provides structured safety information.
