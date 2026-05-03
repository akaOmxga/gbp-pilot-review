import asyncio
import random
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from loguru import logger

P = ParamSpec("P")
R = TypeVar("R")


def with_retry(
    *,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    max_attempts: int = 3,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    jitter: bool = True,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Async retry decorator with exponential backoff and optional jitter."""

    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            attempt = 0
            while True:
                attempt += 1
                try:
                    return await fn(*args, **kwargs)
                except exceptions as exc:
                    if attempt >= max_attempts:
                        logger.warning(
                            "Retry exhausted for {fn} after {n} attempts: {err}",
                            fn=fn.__name__,
                            n=attempt,
                            err=exc,
                        )
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    if jitter:
                        delay *= 0.5 + random.random()
                    logger.info(
                        "Retry {fn} attempt {n}/{max} after {d:.1f}s: {err}",
                        fn=fn.__name__,
                        n=attempt,
                        max=max_attempts,
                        d=delay,
                        err=exc,
                    )
                    await asyncio.sleep(delay)

        return wrapper

    return decorator
