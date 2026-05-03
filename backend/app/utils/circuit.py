from typing import Any

import pybreaker

google_breaker: Any = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="google")
claude_breaker: Any = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=120, name="claude")
resend_breaker: Any = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="resend")
telegram_breaker: Any = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="telegram")
lemonsqueezy_breaker: Any = pybreaker.CircuitBreaker(
    fail_max=5, reset_timeout=60, name="lemonsqueezy"
)


ALL_BREAKERS = {
    "google": google_breaker,
    "claude": claude_breaker,
    "resend": resend_breaker,
    "telegram": telegram_breaker,
    "lemonsqueezy": lemonsqueezy_breaker,
}


def breaker_states() -> dict[str, str]:
    return {name: br.current_state for name, br in ALL_BREAKERS.items()}
