from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.admin import (
    AdminClientNotesUpdate,
    AdminDeletePublishedRequest,
    AdminPublishedDeletionPublic,
    AdminSystemMetrics,
)


def test_notes_update_allows_null() -> None:
    payload = AdminClientNotesUpdate(admin_notes=None)
    assert payload.admin_notes is None


def test_notes_update_enforces_max_length() -> None:
    with pytest.raises(ValidationError):
        AdminClientNotesUpdate(admin_notes="x" * 5001)


def test_delete_published_requires_reason() -> None:
    with pytest.raises(ValidationError):
        AdminDeletePublishedRequest(reason="ab")
    payload = AdminDeletePublishedRequest(reason="contenu erroné")
    assert payload.reason == "contenu erroné"


def test_system_metrics_defaults_are_ints() -> None:
    m = AdminSystemMetrics(
        active_clients=3,
        suspended_clients=0,
        paused_clients=1,
        responses_published_24h=12,
        pending_validation=5,
        dlq_depth=0,
        oauth_alerts=2,
    )
    assert m.active_clients == 3
    assert m.oauth_alerts == 2


def test_published_deletion_public_round_trip() -> None:
    entry = AdminPublishedDeletionPublic(
        id=1,
        actor_user_id=uuid4(),
        response_id=uuid4(),
        review_id=uuid4(),
        client_id=uuid4(),
        reason="erreur de validation",
        created_at=datetime.now(UTC),
    )
    dumped = entry.model_dump()
    assert dumped["reason"] == "erreur de validation"
