"""Application configuration management."""
from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "LabInsight AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_hex(64),
        description="HMAC signing key — MUST be overridden in production.",
    )
    SESSION_COOKIE_NAME: str = "labinsight_session"
    SESSION_MAX_AGE_SECONDS: int = 3600
    CSRF_TOKEN_HEADER: str = "X-CSRF-Token"

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if v in ("CHANGE_ME_generate_with_secrets_token_hex_64", "", "changeme"):
            import warnings
            warnings.warn(
                "SECRET_KEY is using an insecure default. Set a strong SECRET_KEY in production.",
                stacklevel=2,
            )
        return v

    # Database
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "labinsight_db"
    POSTGRES_USER: str = "labinsight_app"
    POSTGRES_PASSWORD: str = Field(default="CHANGE_ME_strong_password_here")
    DATABASE_URL: str = "postgresql+psycopg://labinsight_app:CHANGE_ME@postgres:5432/labinsight_db"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_SESSION_DB: int = 0
    REDIS_RATELIMIT_DB: int = 1

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # Rate Limiting
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_RESET_PER_MINUTE: int = 3
    RATE_LIMIT_GENERAL_PER_MINUTE: int = 120

    # MFA
    MFA_ISSUER_NAME: str = "LabInsight AI"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "/app/uploads"

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"
    MLFLOW_EXPERIMENT_NAME: str = "labinsight_default"

    # Reports
    REPORTS_DIR: str = "/app/generated_reports"
    REPORT_RETENTION_DAYS: int = 30

    # Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@labinsight.dev"
    SMTP_TLS: bool = True

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def cookie_secure(self) -> bool:
        return self.is_production

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
