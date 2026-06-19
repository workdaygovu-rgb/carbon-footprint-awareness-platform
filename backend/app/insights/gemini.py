"""Personalized insights via Google Gemini on Vertex AI.

Design principle: **graceful degradation**. The public entry point,
``generate_insights``, attempts a Gemini call when enabled and *always* falls
back to the deterministic rule-based engine on any error (disabled flag, missing
credentials, network/quota failure, malformed response, validation failure). The
platform therefore never fails to give the user advice, and every code path is
testable without GCP by toggling settings or patching ``_call_gemini``.

Authentication uses Application Default Credentials (the Cloud Run service
account in production) — there is no API key in the codebase.

Changes in v1.2:
- Gemini client cached (avoid re-init credentials per call)
- Output validation (savings bounds, known categories, summary length)
- Structured logging with timing and source field
- Prompt config loaded from versioned YAML
- Async support via asyncio.to_thread

Changes in v1.3:
- TTL response cache (60s) to avoid duplicate Gemini calls for identical inputs
- Source field typed as Literal["gemini", "rules", "cache"]
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import threading
import time
from functools import lru_cache
from pathlib import Path

from cachetools import TTLCache

import yaml

from app.config import Settings
from app.insights.rules import generate_rule_based_insights
from app.models import CarbonInput, FootprintResult, InsightsResponse, Recommendation

logger = logging.getLogger(__name__)

# Known emission categories — used to validate Gemini's output.
_KNOWN_CATEGORIES = frozenset({"transport", "home", "diet", "consumption"})

# Maximum allowed summary length from Gemini (guard against bloated output).
_MAX_SUMMARY_LENGTH = 1000

# Directory containing versioned prompt YAML files.
_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

# TTL cache for insights responses — avoids duplicate Gemini calls when a user
# re-submits identical data within 60 seconds.  Thread-safe via a lock.
_INSIGHTS_CACHE: TTLCache = TTLCache(maxsize=256, ttl=60)
_CACHE_LOCK = threading.Lock()


@lru_cache
def _load_prompt_config(version: str) -> dict:
    """Load and cache the prompt configuration from a versioned YAML file.

    Falls back to the inline defaults if the file is missing, so the system
    keeps working even if the prompt directory is absent (e.g. in tests).
    """
    path = _PROMPTS_DIR / f"{version}.yaml"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    logger.warning("Prompt config %s not found, using inline defaults", path)
    return {}


def _get_system_instruction(config: dict) -> str:
    return config.get(
        "system_instruction",
        "You are a concise, encouraging sustainability coach. Given a person's annual "
        "carbon footprint breakdown (kg CO2e), produce a short summary and 2-4 specific, "
        "realistic actions that target their largest emission sources. Each action must "
        "include an estimated annual saving in kg CO2e. Be practical and non-judgmental.",
    )


def _get_response_schema(config: dict) -> dict:
    return config.get("response_schema", {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "action": {"type": "string"},
                        "estimated_annual_savings_kg": {"type": "number"},
                    },
                    "required": ["category", "action", "estimated_annual_savings_kg"],
                },
            },
        },
        "required": ["summary", "recommendations"],
    })


def _build_prompt(data: CarbonInput, result: FootprintResult) -> str:
    return (
        "Carbon footprint breakdown (kg CO2e per year):\n"
        f"{json.dumps(result.breakdown_kg)}\n"
        f"Total: {result.total_annual_kg} kg/yr ({result.total_annual_tonnes} t/yr).\n"
        f"Sustainable target: {result.comparison.sustainable_target_annual_kg} kg/yr.\n"
        f"Diet: {data.diet.value}. Car fuel: {data.transport.car_fuel.value}.\n"
        "Give tailored advice to reduce the largest sources."
    )


def _validate_gemini_response(
    payload: dict, total_annual_kg: float
) -> None:
    """Validate Gemini's parsed JSON output beyond structural correctness.

    Raises ValueError if any recommendation has impossible savings, an unknown
    category, or the summary is unreasonably long. On failure, the caller
    catches the error and falls back to the rule-based engine.
    """
    summary = payload.get("summary", "")
    if len(summary) > _MAX_SUMMARY_LENGTH:
        raise ValueError(
            f"Gemini summary too long ({len(summary)} chars, max {_MAX_SUMMARY_LENGTH})"
        )

    for rec in payload.get("recommendations", []):
        category = rec.get("category", "")
        if category not in _KNOWN_CATEGORIES:
            raise ValueError(f"Unknown category from Gemini: {category!r}")

        savings = rec.get("estimated_annual_savings_kg", 0)
        if savings <= 0:
            raise ValueError(f"Non-positive savings from Gemini: {savings}")
        if savings > total_annual_kg:
            raise ValueError(
                f"Gemini savings ({savings}) exceed total footprint ({total_annual_kg})"
            )


@lru_cache
def _get_gemini_client(project_id: str, region: str):
    """Return a cached Gemini client (avoids re-initializing credentials per call).

    Imported lazily so the SDK/credentials are only required when actually used —
    keeps unit tests and the rule-based path dependency-free.
    """
    from google import genai

    return genai.Client(vertexai=True, project=project_id, location=region)


def _call_gemini(
    data: CarbonInput, result: FootprintResult, settings: Settings
) -> InsightsResponse:
    """Invoke Gemini on Vertex AI and parse a validated structured response.

    The client is cached so credential loading happens once per process. Output
    is validated for sane values (positive savings within the user's total,
    known categories, bounded summary length) before being returned.
    """
    from google.genai import types

    prompt_config = _load_prompt_config(settings.gemini_prompt_version)

    client = _get_gemini_client(settings.project_id, settings.region)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=_build_prompt(data, result),
        config=types.GenerateContentConfig(
            system_instruction=_get_system_instruction(prompt_config),
            response_mime_type="application/json",
            response_schema=_get_response_schema(prompt_config),
            temperature=prompt_config.get("temperature", 0.4),
            max_output_tokens=prompt_config.get("max_output_tokens", 4096),
        ),
    )
    payload = json.loads(response.text)

    # Validate Gemini output before trusting it — guards against hallucinated
    # or adversarial values (e.g. savings larger than total footprint).
    _validate_gemini_response(payload, result.total_annual_kg)

    recommendations = [
        Recommendation(
            category=str(r["category"]),
            action=str(r["action"]),
            estimated_annual_savings_kg=round(float(r["estimated_annual_savings_kg"]), 2),
        )
        for r in payload.get("recommendations", [])
    ]
    if not recommendations:
        raise ValueError("Gemini returned no recommendations")
    return InsightsResponse(
        summary=str(payload["summary"]),
        recommendations=recommendations[:4],
        source="gemini",
    )


def _cache_key(data: CarbonInput) -> str:
    """Deterministic cache key from the input (SHA-256 of the serialised JSON)."""
    return hashlib.sha256(data.model_dump_json().encode()).hexdigest()


async def generate_insights(
    data: CarbonInput, result: FootprintResult, settings: Settings,
    device_id: str = "",
) -> InsightsResponse:
    """Return personalized insights, preferring Gemini and falling back to rules.

    Checks a 60-second TTL cache first to avoid duplicate Gemini calls when
    the same input is submitted repeatedly.  Runs the (synchronous) Gemini SDK
    call in a thread to avoid blocking the event loop.  Logs timing and source
    as structured JSON fields for observability in Cloud Logging.
    """
    start = time.monotonic()
    # Hash the device_id for logging (privacy: never log raw identifiers).
    id_hash = hashlib.sha256(device_id.encode()).hexdigest()[:12] if device_id else "anon"

    # ── Cache check ──────────────────────────────────────────────────
    cache_key = _cache_key(data)
    with _CACHE_LOCK:
        cached = _INSIGHTS_CACHE.get(cache_key)
    if cached is not None:
        _log_insight(start, "cache", id_hash)
        return InsightsResponse(
            summary=cached.summary,
            recommendations=cached.recommendations,
            source="cache",
        )

    # ── Rules-only path ──────────────────────────────────────────────
    if not settings.use_gemini:
        resp = generate_rule_based_insights(data, result)
        with _CACHE_LOCK:
            _INSIGHTS_CACHE[cache_key] = resp
        _log_insight(start, resp.source, id_hash)
        return resp

    # ── Gemini path (with rules fallback) ────────────────────────────
    try:
        resp = await asyncio.to_thread(_call_gemini, data, result, settings)
    except Exception as exc:  # deliberately broad: any failure must degrade gracefully
        logger.warning(
            "Gemini insight generation failed, using rule-based fallback",
            extra={"error": str(exc), "device_id_hash": id_hash},
        )
        resp = generate_rule_based_insights(data, result)
        _log_insight(start, resp.source, id_hash, fallback=True)
        return resp

    # Store successful result in cache.
    with _CACHE_LOCK:
        _INSIGHTS_CACHE[cache_key] = resp
    _log_insight(start, resp.source, id_hash)
    return resp


def _log_insight(start: float, source: str, id_hash: str, *, fallback: bool = False) -> None:
    """Emit a structured log entry for the insights call."""
    latency_ms = round((time.monotonic() - start) * 1000, 1)
    logger.info(
        "Insight generated",
        extra={
            "endpoint": "/api/insights",
            "latency_ms": latency_ms,
            "source": source,
            "device_id_hash": id_hash,
            "fallback": fallback,
        },
    )
