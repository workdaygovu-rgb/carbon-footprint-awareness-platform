# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres
to [Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-06-12

### Added

- **Streaming body guard**: The body-size middleware now reads actual bytes
  instead of trusting the `Content-Length` header, preventing spoofed or
  omitted headers from bypassing the 64 KB limit. Non-numeric
  `Content-Length` values return 400 instead of crashing.
- **Insights response cache**: 60-second TTL cache (`cachetools.TTLCache`)
  keyed by SHA-256 of the serialized input. Duplicate Gemini calls within
  the TTL window are eliminated, saving Vertex AI cost. Cached responses
  are logged with `source="cache"`.
- **Typed `source` field**: `InsightsResponse.source` changed from `str`
  to `Literal["gemini", "rules", "cache"]` for compile-time safety with
  mypy. Frontend `types.ts` updated to match.
- **ARIA completeness**: Bar chart rows now have `aria-label` with category
  name and value. The total display includes a directional indicator
  (↑ above / ↓ below target) so information is not color-only.
- **E2E in CI**: Playwright test job added to CI (runs on `main` pushes).
- **API drift detection**: CI job that starts the backend, generates
  TypeScript types from OpenAPI, and fails if they differ from committed
  `types.ts`.
- **pytest-asyncio migration**: All async tests use `@pytest.mark.asyncio`
  instead of deprecated `asyncio.get_event_loop().run_until_complete()`.

### Changed

- Bumped version to 1.3.0.
- Added `cachetools==5.5.1` and `pytest-asyncio==0.24.0` to dependencies.

## [1.2.0] - 2026-06-12

### Added

- **Rate limiting** on `/api/insights` (10 req/min per IP via `slowapi`) to
  protect Vertex AI quota and billing from abuse.
- **Request body size guard** (64 KB max) to prevent memory-exhaustion attacks
  from oversized JSON payloads.
- **Structured JSON logging** (`python-json-logger`) with first-class fields:
  `endpoint`, `latency_ms`, `source`, `device_id_hash` — queryable in Cloud
  Logging without free-text parsing.
- **Gemini client caching** (`@lru_cache`) avoids re-initializing credentials
  on every insight request.
- **Gemini output validation**: savings must be positive and less than the
  user's total footprint, categories must be known, summary length is bounded.
  Invalid output triggers the rule-based fallback transparently.
- **Async I/O**: insights and entries endpoints are now `async def`, running
  Gemini and Firestore calls in thread pools to avoid blocking the event loop
  under concurrent load.
- **Prompt versioning**: Gemini system instruction and response schema loaded
  from `app/insights/prompts/v1.yaml` (configurable via `GEMINI_PROMPT_VERSION`).
  Supports A/B testing and rollback without code changes.
- **Dark mode** via `prefers-color-scheme: dark` with complete WCAG AA palette
  (contrast ratios documented inline). Smooth transitions respect
  `prefers-reduced-motion`.
- **Enhanced focus indicators** on table rows and bar-chart elements for
  keyboard navigation.
- **E2E testing** with Playwright: full user flow (fill form → calculate →
  verify results → save → verify history) against the offline dev stack.
- **Supply chain security**: GitHub Actions pinned to full commit SHAs,
  Dependabot config for pip/npm/actions, hash-pinning documentation.
- **API contract sync** tooling: `npm run types:sync` script generates
  TypeScript types from the FastAPI OpenAPI spec for drift detection.
- Prompt evaluation tests: rule engine validated against 3 representative user
  profiles (heavy driver, heavy consumer, energy-heavy household).
- New test files: `test_rate_limit.py`, `test_prompt_config.py`.

### Changed

- `generate_insights` is now async (uses `asyncio.to_thread` for the sync SDK).
- Repository Protocol extended with `async_add` and `async_list_for_device`.
- Both repository implementations (Firestore, in-memory) provide async methods.

## [1.1.0] - 2026-06-11

### Added

- Enforced coverage gates: backend `--cov-fail-under=90` (100% achieved),
  frontend vitest thresholds (≥90% statements / ≥85% branches).
- Backend test suites for the Firestore repository (via fake client), Gemini
  structured-response parsing and fallbacks, SPA static serving, configuration
  parsing, schema bounds, and dependency wiring.
- Frontend test suites for `HistoryPanel`, `InsightsPanel`, `NumberField`,
  device identity, and the API client — with per-component axe accessibility
  assertions.
- ESLint (typescript-eslint, react-hooks, jsx-a11y) and Prettier with CI gates.
- Strict mypy type checking for the backend in CI.
- Screen-reader announcements (`role="status"`) for asynchronous results,
  `aria-busy` on busy buttons, `aria-describedby` hint association, and
  browser-level input bounds mirroring the API schema.
- Project meta: LICENSE (MIT), CONTRIBUTING guide, architecture notes,
  `.editorconfig`, and pre-commit hooks.

### Changed

- Calculator form fields extracted into a reusable, type-safe `NumberField`
  component; app state orchestration extracted into a `useFootprint` hook.
- Rule-engine tuning fractions promoted to named, documented constants.

## [1.0.0] - 2026-06-08

### Added

- Carbon footprint calculation engine with cited emission factors
  (DEFRA 2023, EPA, IPCC / Our World in Data).
- Personalized insights: Gemini on Vertex AI with a deterministic rule-based
  fallback (graceful degradation, response tagged with its source).
- Anonymous tracking history in Firestore keyed by a device id — no accounts,
  no personal data.
- Accessible React + TypeScript SPA: semantic HTML, labelled controls, skip
  link, AA-contrast theme, data-table chart equivalent.
- Single-container deployment to Google Cloud Run (FastAPI serving API + SPA).
