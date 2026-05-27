# FAQ

## What does SightlineAI do?
It provides accessibility-first environmental guidance for blind and visually impaired users.

## Does it work offline?
Yes. It includes deterministic fallback guidance and can be forced via `/api/fallback-guidance`.

## Does it support image input?
Yes, via `/api/analyze-image` and frontend upload controls.

## Does it support voice?
Yes, in browsers that provide speech recognition and synthesis APIs.

## Is geospatial guidance map-accurate?
Not yet. Current implementation is heuristic and safety-conservative.

## Which model does it use?
Qwen through an OpenAI-compatible DashScope endpoint when API key is configured.
