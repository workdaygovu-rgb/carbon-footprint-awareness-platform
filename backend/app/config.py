"""Application configuration via environment variables (12-factor style).

Uses pydantic-settings so configuration is validated and centralised. No secret
values live here — credentials for Vertex AI and Firestore come from Application
Default Credentials (the Cloud Run service account in production, `gcloud auth
application-default login` locally).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application settings, sourced from the environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Google Cloud
    project_id: str = Field(
        default="virtual-prompt-week-3",
        description="Google Cloud project id hosting Vertex AI and Firestore.",
    )
    region: str = Field(
        default="us-central1",
        description="Google Cloud region for Vertex AI and Cloud Run.",
    )

    # Feature flags — let the app degrade gracefully without GCP access.
    use_gemini: bool = Field(
        default=True, description="Whether to call Vertex AI Gemini for personalized insights."
    )
    use_firestore: bool = Field(
        default=True, description="Whether to persist history in Cloud Firestore."
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model identifier on Vertex AI.",
    )

    # Prompt versioning: selects the prompt config file from
    # app/insights/prompts/{version}.yaml. Changed via GEMINI_PROMPT_VERSION.
    gemini_prompt_version: str = Field(
        default="v1",
        description="Prompt config version loaded from app/insights/prompts/{version}.yaml.",
    )

    # CORS (the SPA is same-origin in prod; this matters for local dev).
    allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated list of allowed CORS origins.",
    )

    @property
    def origins_list(self) -> list[str]:
        """Parse the comma-separated CORS origins into a clean list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings singleton (read once per process)."""
    return Settings()
