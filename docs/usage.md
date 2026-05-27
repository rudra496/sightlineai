# Usage Guide

## 1) Start backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 2) Open UI
- Main app: `http://localhost:8000`
- Public site page: `index.html` (GitHub Pages root)

## 3) Text guidance
- Describe your scene
- Optionally provide route/location/hazards
- Click **Analyze scene**

## 4) Forced fallback demo
- Click **Force offline fallback**
- Confirm response `mode` shows `fallback`

## 5) Image guidance
- Upload PNG/JPEG/WEBP image
- Optional hint improves output context

## 6) Voice mode
- Use **Voice input** if browser supports recognition
- Use **Speak guidance** to read output aloud

## 7) Session memory
- View recent outputs in Session memory panel
- Restore or pin important responses
- Clear as needed
