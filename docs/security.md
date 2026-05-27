# Security Notes

## Secrets handling
- API keys are loaded from environment variables only.
- `.env` remains excluded by `.gitignore`.

## Input validation
- Request models enforce constraints via Pydantic.
- Image uploads are size bounded and type-checked using header signature validation.

## Error hygiene
- JSON error schema avoids exposing stack traces.
- Request IDs are attached to responses for traceability.

## Operational guidance
- Keep `QWEN_TIMEOUT_SECONDS` conservative.
- Keep `MAX_IMAGE_BYTES` bounded in production.
- Review fallback output language for safety-critical phrasing.
