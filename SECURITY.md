# Security Policy

## Reporting
If you discover a vulnerability, use GitHub Security Advisories:
https://github.com/rudra496/sightlineai/security/advisories/new

## Current controls
- Environment-only secret configuration
- Structured validation and bounded request payloads
- Safe image upload checks (type + size)
- Consistent JSON error schema with request IDs

## Out of scope
- Any exploit requiring modified local source in a non-default environment.
