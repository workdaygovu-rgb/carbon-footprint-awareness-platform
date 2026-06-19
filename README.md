# 🌱 Carbon Footprint Awareness Platform

[![CI](https://github.com/Auenchanters/Virtual-Prompt-was-Week-3/actions/workflows/ci.yml/badge.svg)](https://github.com/Auenchanters/Virtual-Prompt-was-Week-3/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Virtual PromptWars — Challenge 3.** A web app that helps individuals
> **understand, track, and reduce** their personal carbon footprint through
> simple inputs and **personalized, AI-generated insights**.

Built as a single, accessible web application: a **Python / FastAPI** backend and
a **React + TypeScript** frontend, using **Google Gemini (Vertex AI)** for
personalized advice and **Firestore** for tracking, deployed to **Google Cloud
Run** as one container.

## 🔗 Live demo

**<https://carbon-platform-988953139540.us-central1.run.app>**

> Running on Cloud Run with live Gemini (Vertex AI) insights and Firestore-backed
> tracking in project `virtual-prompt-week-3` (`us-central1`).

---

## 1. Chosen vertical

**Carbon Footprint Awareness Platform** — a tool for everyday individuals (not
corporations) who want to know where their emissions come from and what to
actually *do* about them. The product is organised around the three verbs in the
brief:

| Pillar | In the product |
| --- | --- |
| **Understand** | Enter a few lifestyle facts → get an annual footprint broken down by category, compared to the global average and a Paris-aligned sustainable target. |
| **Track** | Save snapshots over time (anonymously) and see whether your footprint is trending down. |
| **Reduce** | Receive 2–4 personalized, *quantified* actions that target your biggest emission sources first. |

---

## 2. Approach & logic

### The decision flow (smart, context-driven assistant)

```text
User inputs (transport, home, diet, consumption)
        │
        ▼
Carbon engine  ──►  per-category kg CO₂e  ──►  ranked by size
        │                                          │
        ▼                                          ▼
Comparison to targets                  Insights generator
                                         ├─ Gemini (Vertex AI): tailored advice
                                         └─ Rule-based fallback: deterministic,
                                            targets the largest categories
        │
        ▼
Save snapshot (Firestore, keyed by anonymous device id) → history & trend
```

The "logical decision making based on user context" the brief asks for shows up
in two places:

1. **The insights engine ranks the user's own emission categories** and gives
   advice for the biggest contributors — a heavy driver is told about transport;
   a heavy-meat eater is told about diet; each recommendation carries an
   estimated annual saving derived from that user's numbers.
2. **Graceful AI degradation.** Gemini produces the richest, most personal
   advice, but if it is unavailable (no credentials, quota, network, or disabled)
   the platform *transparently falls back* to a deterministic rule engine, so the
   user always gets useful, quantified guidance. The response is tagged with its
   `source` (`gemini` or `rules`).

### Emission model

Footprint figures use published emission factors (UK DEFRA 2023, US EPA, IPCC /
Our World in Data) documented inline in
[`backend/app/carbon/factors.py`](backend/app/carbon/factors.py) — every constant
cites its source rather than being a magic number. All quantities are normalised
to **annual kg CO₂e**.

---

## 3. How the solution works

### Architecture

```text
Browser (React + TS, Vite)              Cloud Run (single container)
  • accessible UI + bar chart  ──HTTP──► FastAPI
  • anonymous device id (localStorage)    ├─ POST /api/calculate  pure carbon engine
                                          ├─ POST /api/insights   Gemini → rules fallback
                                          ├─ POST /api/entries     save snapshot
                                          ├─ GET  /api/entries/{id} history
                                          └─ GET  /  (+ assets)    serves built SPA
                                              │
                                              ├─► Vertex AI (Gemini)  via ADC
                                              └─► Firestore (Native)  via ADC
```

One container serves both the API and the static SPA, so there is a single
service to deploy and a single origin (no CORS in production). Authentication to
Google services uses **Application Default Credentials** (the Cloud Run service
account) — **there are no API keys or secrets in the repository**.

### Project layout

```text
backend/    FastAPI app — carbon engine, insights, repository, routes, tests
frontend/   React + TS SPA — components, hooks, api client, accessible UI, tests
docs/       Architecture notes (docs/ARCHITECTURE.md)
Dockerfile  multi-stage build (node build → python runtime)
.github/    CI: lint + format + types + tests + build on every push to main
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the layering rules and
[CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow.

### Key endpoints

| Method & path | Purpose |
| --- | --- |
| `POST /api/calculate` | Footprint breakdown for the supplied inputs |
| `POST /api/insights` | Personalized reduction advice (Gemini / rules) |
| `POST /api/entries` | Save a snapshot for an anonymous device |
| `GET /api/entries/{device_id}` | List a device's history (newest first) |
| `GET /api/health` | Liveness/readiness probe |

---

## 4. Running locally

**Backend** (Python 3.10+):

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate    # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
# No GCP needed locally — use the rule engine + in-memory store:
USE_GEMINI=false USE_FIRESTORE=false uvicorn app.main:app --reload
```

**Frontend** (Node 20+):

```bash
cd frontend
npm install
npm run dev      # proxies /api to http://localhost:8000
```

**Or the whole thing as one container:**

```bash
docker build -t carbon-platform .
docker run -p 8080:8080 -e USE_GEMINI=false -e USE_FIRESTORE=false carbon-platform
# open http://localhost:8080
```

---

## 5. Testing

| Suite | Command | Covers |
| --- | --- | --- |
| Backend (60 tests, **100% coverage**) | `cd backend && pytest` | carbon math, validation bounds, routes, both repositories (Firestore via fake client), Gemini parsing + fallback, SPA serving |
| Frontend (45 tests, ~99% coverage) | `cd frontend && npm run test:coverage` | every component and hook, API client, device identity, **automated accessibility (axe) per component** |
| Lint | `ruff check .` · `npm run lint` | style, imports, naming, docstrings, complexity, **jsx-a11y accessibility rules** |
| Format | `ruff format --check .` · `npm run format:check` | consistent formatting (ruff format, Prettier) |
| Types | `mypy app` (**strict**) · `npm run typecheck` (strict tsc) | static type correctness end-to-end |

Coverage is enforced, not aspirational: the backend build fails below 90%
(`--cov-fail-under`), and the frontend fails below 90% statements / 85% branches
(vitest `coverage.thresholds`). CI
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs every gate on each
push to `main`.

---

## 6. Deploying to Google Cloud Run

```bash
gcloud config set project virtual-prompt-week-3
gcloud services enable run.googleapis.com aiplatform.googleapis.com \
    firestore.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# Create Firestore (Native mode) once, if it doesn't exist:
gcloud firestore databases create --location=us-central1

# Build + deploy straight from source:
gcloud run deploy carbon-platform \
    --source . --region us-central1 --allow-unauthenticated \
    --set-env-vars PROJECT_ID=virtual-prompt-week-3,REGION=us-central1,USE_GEMINI=true,USE_FIRESTORE=true

# Grant the runtime service account least-privilege access:
#   roles/aiplatform.user  (Gemini)   and   roles/datastore.user  (Firestore)
```

> **Live deployment:** <https://carbon-platform-988953139540.us-central1.run.app>

---

## 7. Assumptions made

- **Awareness, not audit.** Emission factors are representative public averages
  for education, not certified carbon accounting; grids and lifestyles vary, so
  figures are estimates.
- **Anonymous by design.** No login. A random device id (in `localStorage`) keys
  a user's history. This minimises personal data and friction; clearing browser
  storage starts a fresh history.
- **Home energy is shared** across the household size entered, and attributed
  per person.
- **Flights** are entered as counts and converted using representative one-way
  short/long-haul distances.
- **Gemini is best-effort.** When it is unreachable or disabled, the rule-based
  engine guarantees the app still delivers quantified advice.
- **Single region** (`us-central1`) for Cloud Run, Vertex AI, and Firestore.

---

## 8. How this maps to the evaluation rubric

| Axis | Where to look |
| --- | --- |
| **Code Quality** | Typed end-to-end and **statically verified** (strict mypy + strict tsc), layered modules ([docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)), pure functions, ruff + ESLint lint gates, ruff-format + Prettier formatting gates, pre-commit hooks, every constant named and source-cited — no magic numbers. LICENSE, CONTRIBUTING, CHANGELOG maintained. |
| **Security** | ADC (no secrets in repo), bounded input validation, CORS + CSP/security headers, non-root container, pinned deps. |
| **Efficiency** | Stateless pure calc, single slim multi-stage image, cached settings, ~49 kB gzipped bundle. |
| **Testing** | 105 tests across `pytest` + `vitest`, **enforced coverage thresholds** (backend 100% achieved), automated `axe` a11y assertions per component, all gated in CI. |
| **Accessibility** | Semantic HTML, labelled controls with `aria-describedby` hints, skip link, keyboard support, AA-contrast theme, chart with data-table equivalent, `aria-live`/`role="status"` async announcements, `aria-busy` busy states, **jsx-a11y lint rules in CI**. |
| **Google Services** | Cloud Run + Vertex AI (Gemini) + Firestore. |
| **Problem Statement Alignment** | Understand → Track → Reduce loop with personalized, quantified insights. |

---

## License

[MIT](LICENSE) — created for the Virtual PromptWars Challenge 3.
