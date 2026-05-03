from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    secret_key: SecretStr
    frontend_url: str = "http://localhost:3000"

    database_url: PostgresDsn
    redis_url: RedisDsn

    oauth_token_encryption_key: SecretStr

    jwt_secret: SecretStr
    jwt_access_ttl_minutes: int = 60
    jwt_refresh_ttl_days: int = 30

    google_oauth_client_id: SecretStr
    google_oauth_client_secret: SecretStr
    google_oauth_redirect_uri: str

    claude_api_key: SecretStr
    claude_model: str = "claude-sonnet-4-6"

    lemonsqueezy_api_key: SecretStr
    lemonsqueezy_webhook_secret: SecretStr
    lemonsqueezy_store_id: str

    resend_api_key: SecretStr
    resend_from_email: str

    telegram_bot_token: SecretStr | None = None

    sentry_dsn: str | None = None

    celery_task_always_eager: bool = False

    rate_limit_signup_per_hour: int = 3
    rate_limit_login_per_minute: int = 5

    undo_grace_period_minutes: int = Field(default=10, ge=1, le=60)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
