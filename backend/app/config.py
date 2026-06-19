"""Application configuration via environment variables (12-factor style).

Uses pydantic-settings so configuration is validated and centralised. No secret
values live here — credentials for Vertex AI and Firestore come from Application
Default Credentials (the Cloud Run service account in production, `gcloud auth
application-default login` locally).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application settings, sourced from the environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Google Cloud
    project_id: str = "virtual-prompt-week-3"
    region: str = "us-central1"

    # Feature flags — let the app degrade gracefully without GCP access.
    use_gemini: bool = True
    use_firestore: bool = True
    gemini_model: str = "gemini-2.5-flash"

    # Prompt versioning: selects the prompt config file from
    # app/insights/prompts/{version}.yaml. Changed via GEMINI_PROMPT_VERSION.
    gemini_prompt_version: str = "v1"

    # CORS (the SPA is same-origin in prod; this matters for local dev).
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def origins_list(self) -> list[str]:
        """Parse the comma-separated CORS origins into a clean list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings singleton (read once per process)."""
    return Settings()
