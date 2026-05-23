"""Async helper utilities for managing concurrent operations."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

from podifyr.logging import get_logger


logger = get_logger(__name__)

T = TypeVar("T")


async def gather_with_concurrency(
    limit: int,
    tasks: Sequence[Callable[[], Awaitable[T]]],
) -> list[T | BaseException]:
    """Execute async callables with a concurrency limit.

    Unlike asyncio.gather, this uses a semaphore to control
    the maximum number of concurrent operations.

    Args:
        limit: Maximum number of concurrent tasks.
        tasks: Sequence of zero-argument async callables.

    Returns:
        List of results (or exceptions if return_exceptions behavior).
    """
    semaphore = asyncio.Semaphore(limit)
    results: list[T | BaseException] = []

    async def _bounded_task(index: int, task: Callable[[], Awaitable[T]]) -> None:
        async with semaphore:
            try:
                result = await task()
                results.append(result)
            except BaseException as exc:
                logger.warning(
                    "concurrent_task_failed",
                    task_index=index,
                    error=str(exc),
                )
                results.append(exc)

    async with asyncio.TaskGroup() as tg:
        for i, task in enumerate(tasks):
            tg.create_task(_bounded_task(i, task))

    return results
