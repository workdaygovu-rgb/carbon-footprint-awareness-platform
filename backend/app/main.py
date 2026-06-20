"""FastAPI application entry point.

Wires together: security middleware (restrictive CORS + hardening headers), rate
limiting (protects Vertex AI quota), request-size guards, structured JSON
logging, the API routers, and — in production — static serving of the built
React SPA so the whole platform runs as a single Cloud Run container.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pythonjsonlogger.json import JsonFormatter
from slowapi.errors import RateLimitExceeded

from app import __version__
from app.config import get_settings
from app.rate_limit import limiter
from app.routes import calculate, entries, health

# Directory holding the built frontend (populated by the Docker build).
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Maximum request body size in bytes (64 KB). Prevents memory-exhaustion
# attacks from oversized payloads — Pydantic bounds field *values*, but
# the JSON parser must first load the entire body into memory.
_MAX_BODY_BYTES = 64 * 1024

# Security response headers applied to every response (defense in depth).
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; connect-src 'self'; base-uri 'self'; frame-ancestors 'none'"
    ),
}


def _configure_logging() -> None:
    """Set up structured JSON logging for Cloud Logging indexability.

    Fields like ``endpoint``, ``latency_ms``, and ``source`` are logged as
    first-class JSON keys so they can be queried/filtered in Cloud Logging
    without parsing free-text log messages.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "severity"},
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def _register_rate_limit_handler(app: FastAPI) -> None:
    """Attach the SlowAPI rate-limit handler and register the limiter on app state."""

    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(
        request: Request, exc: RateLimitExceeded
    ) -> Response:
        return JSONResponse(
            {"detail": "Rate limit exceeded. Please try again shortly."},
            status_code=429,
            headers={"Retry-After": "60"},
        )


def _add_cors(app: FastAPI, settings: Settings) -> None:
    """Apply restrictive CORS — the SPA is same-origin in production."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )


def _add_security_middleware(app: FastAPI) -> None:
    """Apply defence-in-depth security response headers to every response."""

    @app.middleware("http")
    async def _add_security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for key, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response


def _add_body_size_limiter(app: FastAPI) -> None:
    """Reject POST requests whose body exceeds _MAX_BODY_BYTES.

    Defence-in-depth: Pydantic validates field *values*, but the JSON parser
    must first buffer the entire body into memory. This middleware enforces
    two checks:

    1. **Header check** — fast-reject if Content-Length declares a size above
       the limit (handles well-behaved clients).
    2. **Streaming check** — reads the actual body bytes, aborting with 413
       if the limit is exceeded.
    """

    @app.middleware("http")
    async def _body_size_limiter(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method != "POST":
            return await call_next(request)

        # Fast reject via declared Content-Length (if present and valid).
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > _MAX_BODY_BYTES:
                    return JSONResponse(
                        {"detail": "Request body too large."},
                        status_code=413,
                    )
            except ValueError:
                return JSONResponse(
                    {"detail": "Invalid Content-Length header."},
                    status_code=400,
                )

        # Streaming check: count actual bytes received.
        body = await request.body()
        if len(body) > _MAX_BODY_BYTES:
            return JSONResponse(
                {"detail": "Request body too large."},
                status_code=413,
            )
        return await call_next(request)


def create_app(static_dir: Path | None = None) -> FastAPI:
    """Build the FastAPI application: middleware, routers, and SPA mount.

    Args:
        static_dir: Optional directory containing the built React SPA. Defaults
            to the standard ``static`` folder next to the app package. Exposed
            primarily for tests that want to serve a temporary build.
    """
    _configure_logging()
    settings = get_settings()
    app = FastAPI(
        title="Carbon Footprint Awareness Platform",
        version=__version__,
        description="Understand, track, and reduce your carbon footprint.",
    )

    _register_rate_limit_handler(app)
    _add_cors(app, settings)
    _add_security_middleware(app)
    _add_body_size_limiter(app)

    # API routes.
    app.include_router(health.router)
    app.include_router(calculate.router)
    app.include_router(entries.router)

    _mount_spa(app, static_dir or _STATIC_DIR)
    return app


def _mount_spa(app: FastAPI, static_dir: Path) -> None:
    """Serve the built SPA (if present) with client-side-routing fallback."""
    if not static_dir.exists():
        return

    assets = static_dir / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    index = static_dir / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str) -> Response:
        # API 404s should stay JSON, not fall through to index.html.
        if full_path == "api" or full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = static_dir / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
