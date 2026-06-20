# Contributing

Thanks for your interest in improving the Carbon Footprint Awareness Platform.
This document describes the local workflow and the quality bars every change
must clear — the same gates CI enforces on every push.

## Project layout

```text
backend/    FastAPI app — carbon engine, insights, repositories, routes, tests
frontend/   React + TypeScript SPA — components, hooks, api client, tests
docs/       Architecture notes
Dockerfile  Multi-stage build (node build → python runtime)
```

## Development setup

### Backend (Python 3.10-3.13)

```bash
cd backend
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
USE_GEMINI=false USE_FIRESTORE=false uvicorn app.main:app --reload
```

### Frontend (Node 20+)

```bash
cd frontend
npm install
npm run dev        # proxies /api to http://localhost:8000
```

### Pre-commit hooks (recommended)

```bash
pip install pre-commit
pre-commit install   # runs ruff lint + format on every commit
```

## Quality gates

All of these run in CI ([.github/workflows/ci.yml](.github/workflows/ci.yml))
and must pass before merging:

| Gate | Backend | Frontend |
| --- | --- | --- |
| Lint | `ruff check .` | `npm run lint` (ESLint + jsx-a11y) |
| Format | `ruff format --check .` | `npm run format:check` (Prettier) |
| Types | `mypy app` (strict) | `npm run typecheck` (strict tsc) |
| Tests | `pytest` (coverage gate ≥90%) | `npm run test:coverage` (thresholds ≥90/85) |
| Build | — | `npm run build` |

## Conventions

- **Python:** fully type-annotated, docstrings on public modules/classes/functions,
  emission factors and tuning constants are named and cite their source — no
  magic numbers in logic.
- **TypeScript:** strict mode, no `any`, exported functions and components carry
  JSDoc. Accessibility is part of the definition of done: every component test
  includes an automated axe assertion.
- **Tests first-class:** new behavior ships with tests; coverage thresholds are
  hard CI gates, so untested code fails the build.
- **No secrets in the repo:** Google Cloud auth is via Application Default
  Credentials only.

## Submitting changes

1. Create a feature branch from `main`.
2. Make your change, keeping the gates above green locally.
3. Open a pull request — CI runs the full matrix on every PR.
