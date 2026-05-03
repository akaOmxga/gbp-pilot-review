import random
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.models.enums import PublishDelayRange

_DELAY_RANGES: dict[PublishDelayRange, tuple[timedelta, timedelta]] = {
    PublishDelayRange.range_1h_2h: (timedelta(hours=1), timedelta(hours=2)),
    PublishDelayRange.range_2h_5h: (timedelta(hours=2), timedelta(hours=5)),
    PublishDelayRange.range_5h_1d: (timedelta(hours=5), timedelta(days=1)),
    PublishDelayRange.range_1d_2d: (timedelta(days=1), timedelta(days=2)),
    PublishDelayRange.range_2d_5d: (timedelta(days=2), timedelta(days=5)),
}


def compute_publish_at(
    *,
    now: datetime,
    delay_range: PublishDelayRange,
    window_start: time,
    window_end: time,
    timezone: str,
    rng: random.Random | None = None,
) -> datetime:
    """Compute a publish-at datetime within the configured delay range,
    clamped to the daily publish window in the client's timezone.
    Returned value is UTC.
    """
    rng = rng or random.Random()
    low, high = _DELAY_RANGES[delay_range]
    delta_seconds = rng.randint(int(low.total_seconds()), int(high.total_seconds()))
    candidate = now + timedelta(seconds=delta_seconds)

    tz = ZoneInfo(timezone)
    local = candidate.astimezone(tz)
    local_time = local.time()

    if window_start <= local_time <= window_end:
        return candidate.astimezone(UTC)

    if local_time < window_start:
        target = datetime.combine(local.date(), window_start, tzinfo=tz)
    else:
        next_day: date = local.date() + timedelta(days=1)
        target = datetime.combine(next_day, window_start, tzinfo=tz)

    # Add a random jitter inside the window of [0, 1h]
    jitter = rng.randint(0, 3600)
    target = target + timedelta(seconds=jitter)
    return target.astimezone(UTC)
