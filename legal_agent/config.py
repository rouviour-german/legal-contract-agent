"""Application configuration with validated settings."""

from __future__ import annotations

import enum
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, enum.Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class ContractStage(str, enum.Enum):
    INTAKE = "intake"
    ANALYSIS = "analysis"
    PLAYBOOK = "playbook"
    REDLINE = "redline"
    OBLIGATIONS = "obligations"
    DONE = "done"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LEGAL_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key for Claude")
    openai_api_key: str | None = Field(default=None, description="OpenAI API key for fallback")
    primary_llm: LLMProvider = Field(
        default=LLMProvider.ANTHROPIC,
        description="Primary LLM provider",
    )
    primary_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Primary model identifier",
    )
    fallback_model: str = Field(
        default="gpt-4o",
        description="Fallback model identifier",
    )
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=32_000, gt=0, description="Max output tokens per LLM call")
    per_contract_spend_cap_usd: float = Field(
        default=5.0,
        gt=0,
        description="Maximum LLM spend per contract review (USD)",
    )

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://legal:legal@localhost:5432/legal_contracts",
        description="Async PostgreSQL connection string",
    )

    # --- Redis ---
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string",
    )

    # --- File storage ---
    upload_dir: Path = Field(
        default=Path("uploads"),
        description="Directory for uploaded contract files",
    )
    output_dir: Path = Field(
        default=Path("outputs"),
        description="Directory for generated redlines and exports",
    )
    playbook_dir: Path = Field(
        default=Path("playbooks"),
        description="Directory for playbook YAML files",
    )

    # --- Intake thresholds ---
    intake_confidence_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for autonomous type classification",
    )

    # --- Safety ---
    require_human_on_blocker: bool = Field(
        default=True,
        description="Require human approval for blocker deviations",
    )
    disclaimer_required: bool = Field(
        default=True,
        description="Inject 'not legal advice' disclaimer in all outputs",
    )

    # --- Telemetry ---
    log_level: str = Field(default="INFO", description="Logging level")
    otel_endpoint: str | None = Field(default=None, description="OpenTelemetry collector endpoint")

    @field_validator("upload_dir", "output_dir", "playbook_dir", mode="before")
    @classmethod
    def resolve_path(cls, v: Any) -> Path:
        if isinstance(v, str):
            return Path(v)
        return v

    @property
    def llm_api_key(self) -> str | None:
        """Return the API key for the primary provider."""
        if self.primary_llm == LLMProvider.ANTHROPIC:
            return self.anthropic_api_key
        return self.openai_api_key


settings = Settings()
