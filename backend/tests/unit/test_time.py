import random
from datetime import UTC, datetime, time

from app.models.enums import PublishDelayRange
from app.utils.time import compute_publish_at


def test_compute_publish_at_within_window() -> None:
    rng = random.Random(42)
    now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    out = compute_publish_at(
        now=now,
        delay_range=PublishDelayRange.range_1h_2h,
        window_start=time(9, 0),
        window_end=time(21, 0),
        timezone="Europe/Paris",
        rng=rng,
    )
    assert out > now
    delta = (out - now).total_seconds()
    assert 3600 <= delta <= 3600 * 5  # within bounds + clamp slack


def test_compute_publish_at_clamped_to_window() -> None:
    """If candidate falls in the night, it should clamp to next morning window."""
    rng = random.Random(0)
    # 22:00 Paris time → adding 1-2h would land at 23-24h, outside 09-21h window
    now = datetime(2026, 5, 1, 20, 0, tzinfo=UTC)  # 22h Paris
    out = compute_publish_at(
        now=now,
        delay_range=PublishDelayRange.range_1h_2h,
        window_start=time(9, 0),
        window_end=time(21, 0),
        timezone="Europe/Paris",
        rng=rng,
    )
    from zoneinfo import ZoneInfo

    paris = out.astimezone(ZoneInfo("Europe/Paris"))
    assert paris.hour >= 9
