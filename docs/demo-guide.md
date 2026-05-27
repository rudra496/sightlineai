# Demo Guide for Judges

## Pre-Demo Checklist (2 minutes before)

- [ ] Server is running: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- [ ] Browser open at `http://localhost:8000`
- [ ] Microphone permission granted (for voice demo)
- [ ] Test image file ready (any JPG/PNG of a street, hallway, or intersection)
- [ ] Fallback mode tested (click "Force offline fallback" once)

## 2-Minute Demo Script

### Opening (15 seconds)
> "SightlineAI is an accessibility-first AI assistant for blind and visually impaired users. It provides structured safety guidance through text, voice, and image — and it works offline."

### Demo 1: Text Guidance (30 seconds)
1. Click the **"Station stairs"** example chip
2. Add location: "Train station platform"
3. Click **"Analyze scene"**
4. Point out the structured response: guidance, safety notes, confidence notes, risk score
5. Show the mode badge (Qwen or Fallback)

### Demo 2: Image Analysis (30 seconds)
1. Upload a street/intersection image
2. Add hint: "Busy intersection with construction"
3. Click **"Analyze image"**
4. Show the image summary and guidance

### Demo 3: Voice Input (20 seconds)
1. Click **"Voice input"** button
2. Say: "I'm walking near a construction site with barriers ahead"
3. Show the transcript appearing in the scene field
4. Submit and show response
5. Click **"Speak guidance"** to demonstrate TTS

### Demo 4: Offline Fallback (15 seconds)
1. Click **"Force offline fallback"**
2. Show that guidance still works perfectly without internet
3. Point out the amber "fallback" badge and deterministic risk score

### Demo 5: Memory & History (10 seconds)
1. Show the session memory panel
2. Click "Pin" on an item
3. Click "Restore" to reload a previous session

## Key Talking Points

### Problem
- 2.2 billion people globally have vision impairment (WHO)
- Existing assistive devices cost $3,500+; SightlineAI targets $199
- Most solutions require constant internet — we don't

### Technical Highlights
- Qwen AI with automatic fallback to deterministic guidance
- 20+ hazard category detection
- Geospatial risk scoring (0-100 scale)
- Edge-ready architecture for future wearable integration
- Full offline capability

### Accessibility
- Keyboard-only navigation
- Screen reader compatible
- Voice input/output
- Reduced motion support
- WCAG color contrast compliance

### Security
- Request tracing with unique IDs
- Rate limiting and request size limits
- Secure headers (CSP, X-Frame-Options)
- No credential exposure
- Image validation with magic-byte verification

## Common Judge Questions

**Q: How accurate is the AI guidance?**
A: The confidence_notes field always includes a reliability caveat. In Qwen mode, guidance is AI-generated with safety-first prompting. In fallback mode, deterministic rules provide conservative estimates.

**Q: What's the cost advantage?**
A: 94% cheaper than existing solutions ($199 vs $3,500). The software is open-source and runs on any device with a browser.

**Q: Can it work on a phone?**
A: Yes — the frontend is mobile-responsive and works in mobile browsers. Voice input works in Chrome mobile.

**Q: What's the roadmap for real hardware?**
A: The `/api/edge-context` endpoint is already designed for sensor fusion. Future plans include ESP32 camera modules and smart glasses integration.

**Q: How do you handle privacy?**
A: Images are processed in-memory only, never stored. API keys are server-side only. No tracking or analytics. Self-hostable.

## Demo Tips

- **If internet is unreliable:** Use the fallback button — it's designed for this scenario
- **If voice doesn't work:** Type the scene description manually
- **If image upload fails:** Use a smaller image (under 5 MB)
- **Best impression order:** Text → Image → Voice → Fallback → Memory
