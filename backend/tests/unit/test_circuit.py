import pybreaker
import pytest

from app.utils.circuit import ALL_BREAKERS, breaker_states


def _reset_all() -> None:
    for br in ALL_BREAKERS.values():
        br.close()


def test_breaker_states_returns_all_breakers() -> None:
    _reset_all()
    states = breaker_states()
    assert set(states) == {"google", "claude", "resend", "telegram", "lemonsqueezy"}
    assert all(state == "closed" for state in states.values())


def test_breaker_opens_after_failures() -> None:
    _reset_all()
    br = ALL_BREAKERS["claude"]
    fails_needed = br.fail_max

    def boom() -> None:
        raise RuntimeError("boom")

    # The (fail_max)th call trips the breaker, which raises CircuitBreakerError
    # instead of the underlying RuntimeError. Earlier calls re-raise the original.
    for _ in range(fails_needed - 1):
        with pytest.raises(RuntimeError):
            br.call(boom)
    with pytest.raises(pybreaker.CircuitBreakerError):
        br.call(boom)

    assert br.current_state == "open"
    _reset_all()
