from __future__ import annotations

import sys
from asyncio import Semaphore
from contextvars import Context
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from asyncio import Task, _CoroutineLike
    from types import TracebackType


if sys.version_info < (3, 11):
    from taskgroup import TaskGroup as _TaskGroup
else:
    from asyncio.taskgroups import TaskGroup as _TaskGroup

__all__ = ["TaskGroup"]

T = TypeVar("T")


class TaskGroup(_TaskGroup):
    def __init__(self, *, concurrency_limit: int | None = None) -> None:
        """
        Args:
            concurrency_limit: When provided, use a semaphore to limit the number of
                non-background tasks that run in parallel.

        .. versionchanged:: NEXT
           Added the `concurrency_limit` parameter.
        """
        _TaskGroup.__init__(self)
        self._bg_tasks: set[Task] = set()
        if concurrency_limit is not None and concurrency_limit < 1:
            raise ValueError("concurrency_limit must be >= 1")
        self._semaphore = (
            None if concurrency_limit is None else Semaphore(concurrency_limit)
        )

    def create_task(
        self,
        coro: _CoroutineLike[T],
        *,
        name: str | None = None,
        context: Context | None = None,
    ) -> Task[T]:
        return super().create_task(
            coro if self._semaphore is None else _wrap_coro(coro, self._semaphore),
            name=name,
            context=context,
        )

    def create_background_task(
        self,
        coro: _CoroutineLike[T],
        *,
        name: str | None = None,
        context: Context | None = None,
    ) -> Task[T]:
        """Create, schedule and return a task.

        When the task group shuts down, the task will be cancelled.

        If this task finishes with an error, the entire task group will be
        cancelled, like with non-background tasks.

        Background tasks do not count against the concurrency limit.
        """
        task = _TaskGroup.create_task(self, coro, name=name, context=context)
        if not task.done():
            self._bg_tasks.add(task)
            task.add_done_callback(lambda t: self._bg_tasks.discard(t))
        return task

    async def __aexit__(
        self,
        et: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        for bg_task in self._bg_tasks:
            # Can a task be done without having executed its callbacks?
            # Yes, because callbacks get scheduled, not executed, when
            # it finishes. So a task can still be in _bg_tasks even though
            # it is `.done()`.
            if bg_task.done():
                continue

            bg_task.cancel()

        await _TaskGroup.__aexit__(self, et, exc, tb)


async def _wrap_coro(coro: _CoroutineLike[T], semaphore: Semaphore) -> T:
    async with semaphore:
        return await coro
