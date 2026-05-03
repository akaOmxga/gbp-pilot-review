import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault(
    # Generated via: Fernet.generate_key().decode()
    "OAUTH_TOKEN_ENCRYPTION_KEY", "kHbA6rys1I7sV46M2WI2WY6Sl6NF1m0XRLnXwvTV-HA="
)
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://app:dev@localhost:5432/gbp_review_manager_test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("GOOGLE_OAUTH_CLIENT_ID", "test-google-id")
os.environ.setdefault("GOOGLE_OAUTH_CLIENT_SECRET", "test-google-secret")
os.environ.setdefault(
    "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/v1/oauth/google/callback"
)
os.environ.setdefault("CLAUDE_API_KEY", "test-claude-key")
os.environ.setdefault("LEMONSQUEEZY_API_KEY", "test-ls-key")
os.environ.setdefault("LEMONSQUEEZY_WEBHOOK_SECRET", "test-ls-webhook")
os.environ.setdefault("LEMONSQUEEZY_STORE_ID", "test-store")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("RESEND_FROM_EMAIL", "noreply@example.test")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
