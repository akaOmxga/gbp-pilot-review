import asyncio

import pytest

from app.utils.retry import with_retry


async def test_retry_eventually_succeeds() -> None:
    state = {"calls": 0}

    @with_retry(base_delay=0.01, max_delay=0.05, max_attempts=3)
    async def flaky() -> int:
        state["calls"] += 1
        if state["calls"] < 3:
            raise RuntimeError("not yet")
        return 42

    assert await flaky() == 42
    assert state["calls"] == 3


async def test_retry_exhausts_and_raises() -> None:
    @with_retry(base_delay=0.01, max_delay=0.05, max_attempts=2)
    async def always_bad() -> int:
        raise ValueError("nope")

    with pytest.raises(ValueError):
        await always_bad()


async def test_retry_exception_filter() -> None:
    @with_retry(base_delay=0.01, max_delay=0.02, max_attempts=3, exceptions=(ValueError,))
    async def specific_error() -> int:
        raise TypeError("not retried")

    with pytest.raises(TypeError):
        await specific_error()


_ = asyncio  # silence unused-import in py3.13 strict mode
