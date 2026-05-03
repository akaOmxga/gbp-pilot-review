# 02 — Architecture backend

Document de référence pour la structure du code Python, l'organisation des modules, les conventions de configuration et la stratégie de déploiement applicatif.

## 1. Stack confirmée

| Couche | Choix | Version cible |
|---|---|---|
| Langage | Python | 3.12+ |
| Framework HTTP | FastAPI | 0.110+ |
| ORM | SQLAlchemy | 2.0 (style impératif `Mapped[...]`) |
| Migrations | Alembic | 1.13+ |
| Validation/DTO | Pydantic | 2.x |
| Tâches asynchrones | Celery + Redis | Celery 5.4+, Redis 7 |
| HTTP client | httpx | async, retries via httpx-retry |
| Logging | Loguru | structuré JSON |
| LLM | Anthropic SDK Python | dernière |
| Tests | pytest, pytest-asyncio, factory-boy, respx | |
| Lint/format | ruff, mypy strict | |

Gestion des dépendances via **uv** (rapide, lockfile reproductible).

## 2. Arborescence du projet

```
backend/
├── pyproject.toml
├── uv.lock
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── main.py                  # bootstrap FastAPI (app factory)
│   ├── config.py                # Settings Pydantic
│   ├── database.py              # engine + session factory
│   ├── celery_app.py            # bootstrap Celery + beat schedule
│   ├── logging_config.py        # init Loguru
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── auth.py              # JWT, password hashing (argon2)
│   │   ├── encryption.py        # Fernet wrapper (cf. 01-database.md)
│   │   └── permissions.py       # decorators role-based
│   │
│   ├── models/                  # SQLAlchemy ORM (1 fichier par agrégat)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── client.py
│   │   ├── subscription.py
│   │   ├── oauth_credential.py
│   │   ├── location.py
│   │   ├── review.py
│   │   ├── response.py
│   │   ├── notification.py
│   │   ├── client_settings.py
│   │   ├── prompt_version.py
│   │   ├── audit_log.py
│   │   └── ... (cf. 01-database.md)
│   │
│   ├── schemas/                 # Pydantic DTO (1 fichier par domaine)
│   │   ├── auth.py
│   │   ├── review.py
│   │   ├── response.py
│   │   ├── settings.py
│   │   └── webhook.py
│   │
│   ├── repositories/            # Accès DB pur (1 fichier par modèle)
│   │   ├── base.py              # CRUDRepository générique
│   │   ├── user_repository.py
│   │   ├── client_repository.py
│   │   ├── review_repository.py
│   │   ├── response_repository.py
│   │   ├── oauth_repository.py
│   │   ├── notification_repository.py
│   │   └── quota_repository.py
│   │
│   ├── services/                # Logique métier orchestrée
│   │   ├── auth_service.py
│   │   ├── oauth_service.py
│   │   ├── polling_service.py
│   │   ├── filtering_service.py
│   │   ├── generation_service.py
│   │   ├── publication_service.py
│   │   ├── notification_service.py
│   │   ├── subscription_service.py
│   │   ├── quota_service.py
│   │   └── prompt_service.py
│   │
│   ├── integrations/            # Adapters APIs externes
│   │   ├── google_business/
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py       # interface Protocol
│   │   │   ├── client.py        # impl httpx
│   │   │   ├── exceptions.py
│   │   │   └── schemas.py       # mapping API Google
│   │   ├── claude/
│   │   │   ├── adapter.py
│   │   │   └── client.py
│   │   ├── lemonsqueezy/
│   │   │   ├── client.py
│   │   │   └── webhooks.py      # vérif HMAC + parsing
│   │   ├── resend/
│   │   │   └── client.py
│   │   └── telegram/
│   │       └── client.py
│   │
│   ├── tasks/                   # Tâches Celery
│   │   ├── __init__.py
│   │   ├── polling_tasks.py
│   │   ├── generation_tasks.py
│   │   ├── publication_tasks.py
│   │   ├── notification_tasks.py
│   │   ├── oauth_tasks.py
│   │   ├── maintenance_tasks.py # purge RGPD, agrégations quota
│   │   └── digest_tasks.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # Depends() FastAPI
│   │   ├── router.py            # agrège tous les sous-routers
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── oauth.py
│   │       ├── reviews.py
│   │       ├── responses.py
│   │       ├── settings.py
│   │       ├── notifications.py
│   │       ├── subscription.py
│   │       ├── webhooks.py      # /webhooks/lemonsqueezy
│   │       ├── me.py            # profil + export RGPD
│   │       └── admin/
│   │           ├── clients.py
│   │           ├── validation_queue.py
│   │           ├── monitoring.py
│   │           └── deletions.py
│   │
│   ├── events/                  # bus interne lightweight
│   │   ├── dispatcher.py
│   │   └── handlers.py
│   │
│   └── utils/
│       ├── retry.py             # @with_retry decorator
│       ├── correlation.py       # context var correlation_id
│       ├── time.py              # utilitaires fenêtres horaires
│       └── language.py          # détection de langue
│
└── tests/
    ├── conftest.py
    ├── unit/
    ├── integration/
    └── e2e/
```

## 3. Pattern d'architecture en couches

```
HTTP request
  │
  ▼
api/v1/<endpoint>.py        ← validation Pydantic, auth, autorisation
  │
  ▼
services/<service>.py        ← logique métier, orchestration multi-repos
  │
  ├──► repositories/<repo>.py ← SQL pur via SQLAlchemy
  │
  └──► integrations/<adapter>.py ← APIs externes (Google, Claude, etc.)
```

**Règles strictes** :

- `api/` n'importe **jamais** de `repositories/` directement. Tout passe par `services/`.
- `services/` n'écrit **jamais** de SQL brut ni d'appel HTTP externe. Délégation systématique.
- `repositories/` ne dépend **jamais** de `services/` (pas de cycle).
- `integrations/` expose une interface (Protocol Python typé), permettant le mock en test.
- Les tâches Celery dans `tasks/` sont de fines enveloppes : elles instancient une session DB, appellent un service, gèrent retries.

### Exemple de chaîne — validation d'une réponse par le client

```
POST /api/v1/responses/{id}/approve
  │
  ▼ api/v1/responses.py::approve_response
      - Pydantic valide le path param
      - deps.get_current_client_user() → User
      - delegate to services.publication_service.schedule_publication(response_id, user)
  │
  ▼ services/publication_service.py::schedule_publication
      - response_repository.get_owned_by_client(response_id, client_id)
      - vérifie statut éligible (pending_validation_*)
      - calcule scheduled_at via utils.time.compute_publish_at(...)
      - response_repository.transition_to_scheduled(response, scheduled_at)
      - events.dispatch("response.scheduled", response_id)
  │
  ▼ events.handlers
      - notification_service.dispatch("response_scheduled", client_id, payload)
```

## 4. Configuration

`backend/app/config.py` :

```python
from functools import lru_cache
from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # core
    environment: str = Field(default="development")  # development|staging|production
    debug: bool = False
    secret_key: SecretStr  # JWT signing
    frontend_url: str

    # storage
    database_url: PostgresDsn
    redis_url: RedisDsn

    # encryption
    oauth_token_encryption_key: SecretStr  # base64 url-safe 32 bytes

    # Google OAuth
    google_oauth_client_id: SecretStr
    google_oauth_client_secret: SecretStr
    google_oauth_redirect_uri: str

    # Claude
    claude_api_key: SecretStr
    claude_model: str = "claude-sonnet-4-6"

    # Lemon Squeezy
    lemonsqueezy_api_key: SecretStr
    lemonsqueezy_webhook_secret: SecretStr
    lemonsqueezy_store_id: str

    # Notifications
    resend_api_key: SecretStr
    resend_from_email: str
    telegram_bot_token: SecretStr | None = None

    # Observability
    sentry_dsn: str | None = None
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

Aucune variable d'environnement référencée ailleurs que dans `Settings`. Pas de `os.getenv()` en libre-service dans le code.

Les `SecretStr` empêchent le leak accidentel via `repr()` ou logs.

## 5. Celery — configuration et beat schedule

```python
# backend/app/celery_app.py
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "gbp_review_manager",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
    include=[
        "app.tasks.polling_tasks",
        "app.tasks.generation_tasks",
        "app.tasks.publication_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.oauth_tasks",
        "app.tasks.maintenance_tasks",
        "app.tasks.digest_tasks",
    ],
)

celery_app.conf.update(
    task_default_queue="default",
    task_routes={
        "app.tasks.polling_tasks.*": {"queue": "polling"},
        "app.tasks.generation_tasks.*": {"queue": "generation"},
        "app.tasks.publication_tasks.*": {"queue": "publication"},
        "app.tasks.notification_tasks.*": {"queue": "notification"},
    },
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # éviter qu'un worker bloque la queue
    timezone="UTC",
)

celery_app.conf.beat_schedule = {
    "poll-active-clients": {
        "task": "app.tasks.polling_tasks.dispatch_pollings",
        "schedule": crontab(minute="*/15"),
    },
    "publication-dispatcher": {
        "task": "app.tasks.publication_tasks.dispatch_due_publications",
        "schedule": crontab(minute="*"),
    },
    "refresh-expiring-oauth": {
        "task": "app.tasks.oauth_tasks.refresh_expiring_tokens",
        "schedule": crontab(minute="*/30"),
    },
    "send-daily-digests": {
        "task": "app.tasks.digest_tasks.send_pending_digests",
        "schedule": crontab(minute="*/15"),  # le job filtre l'heure préférée client
    },
    "purge-expired-data": {
        "task": "app.tasks.maintenance_tasks.purge_expired_data",
        "schedule": crontab(hour=3, minute=15),
    },
    "aggregate-quota-alerts": {
        "task": "app.tasks.maintenance_tasks.check_quota_thresholds",
        "schedule": crontab(hour=9, minute=0),
    },
}
```

**Queues séparées** : `polling`, `generation`, `publication`, `notification`, `default`. Permet de dimensionner les workers indépendamment (ex : 1 worker `generation` à concurrency=2 pour ne pas exploser le quota Claude, vs 4 workers `notification` à concurrency=10).

**Topology recommandée sur le VPS** :
- 1 worker beat (`celery -A app.celery_app beat`)
- 1 worker `polling,default` (concurrency 2)
- 1 worker `generation` (concurrency 2)
- 1 worker `publication,notification` (concurrency 4)
- Flower exposé sur un sous-domaine admin protégé par auth basique

## 6. Stratégie de retry et circuit breaker

### Décorateur `@with_retry`

```python
# backend/app/utils/retry.py
from functools import wraps
from typing import Callable, Type
import asyncio
import random

from loguru import logger


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    on: tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True,
):
    def decorator(fn: Callable):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                try:
                    return await fn(*args, **kwargs)
                except on as exc:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.bind(attempts=attempt).exception(
                            "retry exhausted in {fn}", fn=fn.__name__
                        )
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    if jitter:
                        delay *= 0.5 + random.random()
                    logger.warning(
                        "retrying {fn} (attempt={attempt}, delay={delay:.1f}s): {exc}",
                        fn=fn.__name__, attempt=attempt, delay=delay, exc=exc,
                    )
                    await asyncio.sleep(delay)
        return wrapper
    return decorator
```

### Circuit breaker — `pybreaker`

Un circuit breaker par intégration externe (`google_business`, `claude`, `lemonsqueezy`). Configuré dans le client : `fail_max=5, reset_timeout=60s`. Si ouvert, les tâches Celery échouent en `Reject` et seront re-essayées plus tard.

### Dead Letter Queue

Handler global Celery sur `task_failure_signal` qui, si `attempts >= max_retries`, sérialise le job (`task_name`, `args`, `kwargs`, `traceback`) dans la table `dead_letter_jobs`. Une vue admin (`/admin/monitoring`) expose cette table avec un bouton "rejouer" qui ré-enqueue la tâche.

## 7. Logging structuré (Loguru)

```python
# backend/app/logging_config.py
import sys
from contextvars import ContextVar
from loguru import logger

correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def correlation_filter(record):
    record["extra"]["correlation_id"] = correlation_id_var.get()
    return True


def configure_logging(level: str = "INFO"):
    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        serialize=True,  # JSON output
        filter=correlation_filter,
    )
```

**Champs systématiques** dans `logger.bind(...)` : `client_id`, `review_id`, `response_id`, `task_name`, `correlation_id`. Middleware FastAPI génère un `correlation_id` par requête (UUID v7) et le propage. Les tâches Celery héritent du `correlation_id` via headers de message.

**Interdits** : tokens OAuth, refresh tokens, payloads webhooks complets (extraire les champs utiles uniquement), mots de passe.

## 8. Interfaces clés (contracts d'intégration)

### `GoogleBusinessAdapter`

```python
# backend/app/integrations/google_business/adapter.py
from typing import Protocol
from app.integrations.google_business.schemas import (
    GoogleAccount, GoogleLocation, GoogleReview,
)


class GoogleBusinessAdapter(Protocol):
    async def list_accounts(self, access_token: str) -> list[GoogleAccount]: ...

    async def list_locations(
        self, access_token: str, account_id: str
    ) -> list[GoogleLocation]: ...

    async def list_reviews(
        self,
        access_token: str,
        account_id: str,
        location_id: str,
        page_size: int = 50,
        page_token: str | None = None,
    ) -> tuple[list[GoogleReview], str | None]: ...

    async def reply_to_review(
        self, access_token: str, review_resource_name: str, content: str
    ) -> GoogleReview: ...

    async def delete_reply(
        self, access_token: str, review_resource_name: str
    ) -> None: ...
```

### `LLMProvider`

```python
# backend/app/integrations/claude/adapter.py
from dataclasses import dataclass
from typing import Protocol


@dataclass
class AIResponse:
    status: int       # 0 = refus, 1 = succès
    content: str
    details: str | None
    tokens_input: int
    tokens_output: int
    model: str


class LLMProvider(Protocol):
    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> AIResponse: ...
```

### `NotificationChannel`

```python
# backend/app/integrations/_notifications.py
from dataclasses import dataclass
from typing import Protocol


@dataclass
class NotificationResult:
    success: bool
    provider_message_id: str | None
    error: str | None


class NotificationChannel(Protocol):
    channel_name: str

    async def send(
        self, recipient: str, subject: str, body_html: str, body_text: str
    ) -> NotificationResult: ...
```

Ajouter un canal SMS (V2) = créer `app/integrations/twilio/` qui implémente `NotificationChannel`. Aucun changement dans les services métier.

## 9. Sécurité backend

- **Auth** : JWT signés HS256, expiration 1h, refresh token 30j stocké HTTP-only cookie. Hash mot de passe argon2id.
- **Rate limiting** : `slowapi` sur `/api/v1/auth/login` (5/min/IP), `/api/v1/auth/signup` (3/h/IP), webhooks publics (60/min/IP).
- **CORS** : whitelist exclusive sur `settings.frontend_url`, credentials autorisés.
- **CSRF** : pas nécessaire avec JWT en header `Authorization`. Pour les cookies, double submit token.
- **Webhooks Lemon Squeezy** : vérification HMAC-SHA256 du header `X-Signature` avant parsing du body. Idempotence via `webhook_events.event_id`.
- **OAuth state** : signé HMAC avec `secret_key`, contient `client_id` + nonce + expiration 10 min.
- **Permissions** : décorateur `@require_role("admin")` sur les endpoints admin. Un client ne peut accéder qu'à ses propres ressources (filtre `client_id = current_user.client_id` systématique dans les repositories).

## 10. Tests

### Pyramide

| Niveau | Volume cible | Outils |
|---|---|---|
| Unitaires | ~70% des tests | pytest, factory-boy |
| Intégration (DB + Redis réels) | ~25% | pytest + testcontainers ou docker-compose-test |
| End-to-end (HTTP réels mockés) | ~5% | pytest + respx |

### Conventions

- Pas de mocks sur la DB. Une DB Postgres dédiée tests (transaction rollback par test via `SAVEPOINT`).
- Toutes les intégrations externes (Google, Claude, Lemon Squeezy, Resend) sont **mockées via leur Protocol** : on injecte un fake en test, jamais d'appel réseau.
- `factories/` génère des objets ORM cohérents (`ClientFactory`, `ReviewFactory`, etc.).
- Tests Celery avec `task_always_eager=True` pour les tests de logique ; un test e2e avec un worker réel pour valider la sérialisation des tâches.

## 11. Bootstrap et lancement local

```yaml
# docker-compose.yml (extrait, à étoffer en Phase 2)
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: gbp_review_manager
      POSTGRES_USER: app
      POSTGRES_PASSWORD: dev
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  api:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --reload
    env_file: ./backend/.env
    depends_on: [postgres, redis]
    ports: ["8000:8000"]

  worker:
    build: ./backend
    command: celery -A app.celery_app worker -Q polling,generation,publication,notification,default --concurrency 4
    env_file: ./backend/.env
    depends_on: [postgres, redis]

  beat:
    build: ./backend
    command: celery -A app.celery_app beat
    env_file: ./backend/.env
    depends_on: [redis]
```

Commandes utiles :

```bash
uv sync                                      # install deps
uv run alembic upgrade head                  # migrations
uv run uvicorn app.main:app --reload         # API en local
uv run celery -A app.celery_app worker -Q polling,generation,publication,notification
uv run celery -A app.celery_app beat
uv run pytest                                # tests
uv run ruff check . && uv run mypy app       # lint + types
```
