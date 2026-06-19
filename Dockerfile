# ─────────────────────────────────────────────────────────────────────────
# Multi-stage build: compile the React SPA, then ship a slim Python image that
# serves both the API and the static frontend as a single Cloud Run container.
# ─────────────────────────────────────────────────────────────────────────

# Stage 1 — build the frontend
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2 — runtime: Python + FastAPI serving API and built SPA
FROM python:3.12-slim AS runtime

# Avoid .pyc files and force unbuffered logs (better for Cloud Run logging).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install dependencies first to leverage Docker layer caching.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application code and the built frontend.
COPY backend/app ./app
COPY --from=frontend /frontend/dist ./static

# Run as a non-root user (security hardening).
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8080

# Bind to Cloud Run's $PORT. JSON form with `sh -c` so the env var is expanded
# at runtime and signals propagate correctly via exec.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
