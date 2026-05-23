"""Retry utilities with exponential backoff for resilient API calls."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from podifyr.core.constants import DEFAULT_MAX_RETRIES, DEFAULT_RETRY_BASE_DELAY
from podifyr.logging import get_logger


logger = get_logger(__name__)

T = TypeVar("T")


def async_retry_with_backoff(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_RETRY_BASE_DELAY,
    max_delay: float = 30.0,
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for async functions providing retry with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds (doubles each retry).
        max_delay: Maximum delay cap in seconds.
        retryable_exceptions: Tuple of exception types that trigger a retry.

    Returns:
        Decorated async function with retry logic.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: BaseException | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exception = exc
                    if attempt == max_retries:
                        break

                    delay = min(base_delay * (2**attempt), max_delay)
                    logger.warning(
                        "retry_scheduled",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay_seconds=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)

            logger.error(
                "retries_exhausted",
                function=func.__name__,
                max_retries=max_retries,
                final_error=str(last_exception),
            )
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator


def sync_retry_with_backoff(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_RETRY_BASE_DELAY,
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for synchronous functions providing retry with exponential backoff."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            import time

            last_exception: BaseException | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exception = exc
                    if attempt == max_retries:
                        break

                    delay = min(base_delay * (2**attempt), 30.0)
                    logger.warning(
                        "sync_retry_scheduled",
                        function=func.__name__,
                        attempt=attempt + 1,
                        delay_seconds=delay,
                    )
                    time.sleep(delay)

            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator
