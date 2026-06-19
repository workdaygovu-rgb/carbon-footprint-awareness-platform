# Architecture

A single Cloud Run container serves both the API and the built SPA, keeping
deployment, origin, and operations simple. This document explains the layers
and the reasoning behind them; see the [README](../README.md) for product
context and deployment steps.

## System overview

```text
Browser (React + TS, Vite)              Cloud Run (single container)
  • accessible UI + bar chart  ──HTTP──► FastAPI
  • anonymous device id (localStorage)    ├─ POST /api/calculate   pure carbon engine
                                          ├─ POST /api/insights    Gemini → rules fallback
                                          ├─ POST /api/entries     save snapshot
                                          ├─ GET  /api/entries/{id} history
                                          └─ GET  /  (+ assets)    serves built SPA
                                              │
                                              ├─► Vertex AI (Gemini)  via ADC
                                              └─► Firestore (Native)  via ADC
```

## Backend layers

| Layer | Module(s) | Rule |
| --- | --- | --- |
| Domain (pure) | `app/carbon/` | Deterministic math, no I/O. Every emission factor is a named constant citing its source. |
| Insights | `app/insights/` | `gemini.py` calls Vertex AI; `rules.py` is the always-available deterministic fallback. The public entry point never raises — it degrades. |
| Persistence | `app/repository/` | A `Protocol` interface with two implementations: Firestore (production) and in-memory (dev/tests). Selected by configuration, injected via FastAPI `Depends`. |
| Transport | `app/routes/`, `app/models.py` | Thin routes; Pydantic schemas validate and bound every input at the edge. |
| Composition | `app/main.py`, `app/deps.py`, `app/config.py` | App factory wires middleware (CORS, security headers), routers, and the SPA mount. |

Design rules the codebase follows:

- **Dependencies point inward.** Routes depend on the repository *interface*,
  never a concrete backend; the domain layer imports nothing above it.
- **Graceful degradation.** Gemini and Firestore are feature-flagged
  (`USE_GEMINI`, `USE_FIRESTORE`); the platform stays fully functional with
  both disabled, which is also how the test suite runs (no GCP needed).
- **Lazy cloud imports.** GCP SDKs are imported inside the code paths that use
  them, so local development and CI never need credentials.
- **No secrets.** All Google Cloud auth is Application Default Credentials.

## Frontend structure

| Concern | Location |
| --- | --- |
| State + API orchestration | `src/hooks/useFootprint.ts` |
| Presentation | `src/components/` (each with its own test + axe assertion) |
| API client / types / formatting | `src/lib/` (types mirror the Pydantic schemas) |

`App.tsx` composes the hook and the components; reusable form markup lives in
`NumberField`, which owns label/hint/ARIA wiring so accessibility is consistent
by construction.

## Quality gates

Every push runs lint (ruff, ESLint + jsx-a11y), formatting (ruff format,
Prettier), strict type checks (mypy, tsc), and both test suites with enforced
coverage thresholds — see [CONTRIBUTING.md](../CONTRIBUTING.md).
