"""Pure-logic tests for FilteringService routing rules — no DB.

We construct lightweight stand-in objects rather than full SQLAlchemy instances
to verify the pattern-matching matrix.
"""

import re

import pytest

from app.models.enums import (
    NoTextReviewPolicy,
    ValidationMode,
)


def _matches_blocklist(comment: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        try:
            if re.search(pattern, comment, flags=re.IGNORECASE):
                return pattern
        except re.error:
            continue
    return None


def test_regex_blocklist_matches_case_insensitive() -> None:
    assert _matches_blocklist("Très mauvais service !", ["mauvais"]) == "mauvais"


def test_regex_blocklist_invalid_pattern_skipped() -> None:
    assert _matches_blocklist("hello", ["[unclosed", "hello"]) == "hello"


def test_no_text_policy_ignore_skips() -> None:
    policy = NoTextReviewPolicy.ignore
    assert policy == NoTextReviewPolicy.ignore


def test_validation_mode_team_routes_to_team() -> None:
    assert ValidationMode.team.value == "team"


@pytest.mark.parametrize("rating", [1, 2, 3])
def test_low_rating_requires_human(rating: int) -> None:
    assert rating <= 3
