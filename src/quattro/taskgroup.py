from __future__ import annotations

import sys
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
    def __init__(self) -> None:
        _TaskGroup.__init__(self)
        self._bg_tasks: set[Task] = set()

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
        """
        task = self.create_task(coro, name=name, context=context)
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
