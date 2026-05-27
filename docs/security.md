# Security Documentation

> Comprehensive security overview for SightlineAI.

---

## Threat Model

| Threat | Risk Level | Mitigation |
|---|---|---|
| **API key exposure** | High | Environment-only configuration; `.env` in `.gitignore`; no keys in code or responses |
| **Malicious file upload** | Medium | MIME type allowlist + header signature validation + size bounds |
| **Denial of service** | Medium | Rate limiting (60 req/min/IP) + request size limits (10 MB) |
| **Input injection** | Medium | Pydantic strict validation + string length constraints |
| **Path traversal** | Medium | Resolved path checking for static file serving |
| **Cross-site scripting** | Low | CSP headers; no raw user HTML rendered |
| **Man-in-the-middle** | Low | HTTPS recommended for production; non-HTTPS config warnings |
| **Session data loss** | Low | In-memory store (acceptable for current scope); client-side localStorage backup |

---

## Security Measures Checklist

- [x] API keys loaded from environment variables only
- [x] `.env` file excluded via `.gitignore`
- [x] Pydantic schema validation on all endpoints
- [x] Image MIME type allowlist (JPEG, PNG, WEBP)
- [x] Image header signature verification (prevents MIME spoofing)
- [x] Image upload size limit (configurable, default 5 MB)
- [x] Request body size limit (10 MB for non-upload endpoints)
- [x] Rate limiting (60 requests/minute per IP)
- [x] Structured JSON error schema (no stack traces)
- [x] Request ID tracking on all responses
- [x] `X-Content-Type-Options: nosniff` header
- [x] `X-Frame-Options: DENY` header
- [x] `Referrer-Policy: strict-origin-when-cross-origin` header
- [x] `Content-Security-Policy` header
- [x] CORS restricted in production mode (`PRODUCTION=true`)
- [x] Path traversal protection for static file serving
- [x] No committed secrets in repository history
- [x] Conservative timeout defaults (25s)
- [x] Config validation with warnings for suspicious values

---

## Responsible Disclosure Policy

If you discover a security vulnerability in SightlineAI:

1. **Do not** open a public GitHub issue
2. Report via [GitHub Security Advisories](https://github.com/rudra496/sightlineai/security/advisories/new)
3. Include: description, reproduction steps, potential impact, suggested fix (if any)
4. We will acknowledge within 48 hours and aim to resolve within 7 days
5. We ask that you give us reasonable time to fix before public disclosure

**In scope:**
- Server-side request injection or manipulation
- Authentication/authorization bypass (when applicable)
- File upload vulnerabilities
- Data exposure or information leakage
- Denial of service vulnerabilities

**Out of scope:**
- Issues requiring modified local source code
- Attacks requiring physical access to the server
- Social engineering
- Theoretical vulnerabilities without proof of exploitation

---

## Dependency Security

### Direct Dependencies

| Package | Purpose | Security Notes |
|---|---|---|
| `fastapi` | Web framework | Actively maintained, automatic security patches |
| `uvicorn` | ASGI server | Production-grade, well-audited |
| `pydantic` | Data validation | Strict mode prevents many injection vectors |
| `python-dotenv` | Environment loading | Only reads local `.env`, no network calls |
| `httpx` | HTTP client (for Qwen API) | Async-capable, TLS verification enabled |

### Best Practices

- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Review `pip audit` output regularly
- Pin versions in `requirements.txt` for reproducible builds
- No JavaScript dependencies in the frontend (zero supply chain risk)

---

## API Security Considerations

### Rate Limiting

- **Limit:** 60 requests per minute per client IP
- **Enforcement:** In-memory sliding window
- **Response:** HTTP 429 with `Retry-After` header
- **Note:** Rate limit state resets on server restart

### Input Validation

All inputs are validated through Pydantic schemas with:
- **Type enforcement** — incorrect types are rejected
- **Length constraints** — `min_length` and `max_length` on all string fields
- **Range constraints** — numeric fields have `ge`/`le` bounds
- **Enum constraints** — `Literal` types restrict to valid values

### Image Upload Security

Three-layer defense:
1. **Extension check** — file extension validated against allowlist
2. **MIME type check** — Content-Type header validated
3. **Signature verification** — file header bytes checked against known magic numbers

This prevents:
- Polyglot file attacks (file is both valid image and executable)
- MIME type spoofing (claiming to be JPEG but isn't)
- Oversized file denial of service

### CORS Policy

- **Development mode** (default): `allow_origins=["*"]` for local testing
- **Production mode** (`PRODUCTION=true`): `allow_origins=[]` — same-origin only
- Credentials are never allowed cross-origin

### Response Headers

Every response includes security headers:

```
X-Request-ID: <uuid>
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;
```

---

## Production Deployment Checklist

- [ ] Set `PRODUCTION=true` environment variable
- [ ] Configure `DASHSCOPE_API_KEY` (never commit to version control)
- [ ] Set `MAX_IMAGE_BYTES` appropriately for your use case
- [ ] Run behind a reverse proxy (nginx/Caddy) with TLS
- [ ] Set `QWEN_TIMEOUT_SECONDS` conservatively (≤30s)
- [ ] Review and tighten CSP headers for your domain
- [ ] Enable request logging to external monitoring
- [ ] Consider adding authentication for public deployments
