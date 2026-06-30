import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def should_retry(status_code: int) -> bool:
    return status_code in _RETRYABLE_STATUSES


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> float:
    delay = min(base_delay * (2**attempt), max_delay)
    if jitter:
        delay *= 0.5 + random.random() * 0.5
    return delay  # type: ignore[no-any-return]


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_statuses: set[int] | None = None,
) -> Callable[[F], F]:
    statuses = retryable_statuses or _RETRYABLE_STATUSES

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    status_code = getattr(e, "response", None)
                    status_code = getattr(status_code, "status_code", 0) if status_code else 0

                    if status_code and status_code in statuses and attempt < max_retries:
                        delay = exponential_backoff(attempt, base_delay, max_delay)
                        time.sleep(delay)
                        continue

                    if attempt < max_retries:
                        delay = exponential_backoff(attempt, base_delay, max_delay)
                        time.sleep(delay)
                        continue

                    raise

            raise last_error  # type: ignore

        return wrapper  # type: ignore

    return decorator
