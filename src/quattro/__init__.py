"""Task control for asyncio."""
from __future__ import annotations

import sys
from collections.abc import Awaitable, Coroutine, Generator
from typing import Any, Literal, TypeAlias, TypeVar, overload

from .cancelscope import (
    CancelScope,
    cancel_stack,
    fail_after,
    fail_at,
    move_on_after,
    move_on_at,
)
from .taskgroup import TaskGroup

__all__ = [
    "CancelScope",
    "fail_after",
    "fail_at",
    "gather",
    "get_current_effective_deadline",
    "move_on_after",
    "move_on_at",
    "TaskGroup",
    "TaskGroupError",
]


def get_current_effective_deadline() -> float:
    return min(
        [cs._deadline for cs in cancel_stack.get() if cs._deadline is not None],
        default=float("inf"),
    )


# Type hints taken from https://github.com/python/typeshed/blob/main/stdlib/asyncio/tasks.pyi,
# bless their hearts.
_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")
_T4 = TypeVar("_T4")
_T5 = TypeVar("_T5")
_T6 = TypeVar("_T6")

if sys.version_info >= (3, 12):
    _AwaitableLike: TypeAlias = Awaitable[_T]
    _CoroutineLike: TypeAlias = Coroutine[Any, Any, _T]
else:
    _AwaitableLike: TypeAlias = Generator[Any, None, _T] | Awaitable[_T]
    _CoroutineLike: TypeAlias = Generator[Any, None, _T] | Coroutine[Any, Any, _T]


@overload
async def gather(  # type: ignore[overload-overlap]
    coro: _CoroutineLike[_T1], *, return_exceptions: Literal[False] = False
) -> tuple[_T1]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: _CoroutineLike[_T1],
    __coro_or_future2: _CoroutineLike[_T2],
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: _CoroutineLike[_T1],
    __coro_or_future2: _CoroutineLike[_T2],
    __coro_or_future3: _CoroutineLike[_T3],
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: _CoroutineLike[_T1],
    __coro_or_future2: _CoroutineLike[_T2],
    __coro_or_future3: _CoroutineLike[_T3],
    __coro_or_future4: _CoroutineLike[_T4],
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3, _T4]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: _CoroutineLike[_T1],
    __coro_or_future2: _CoroutineLike[_T2],
    __coro_or_future3: _CoroutineLike[_T3],
    __coro_or_future4: _CoroutineLike[_T4],
    __coro_or_future5: _CoroutineLike[_T5],
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3, _T4, _T5]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: _CoroutineLike[_T1],
    __coro_or_future2: _CoroutineLike[_T2],
    __coro_or_future3: _CoroutineLike[_T3],
    __coro_or_future4: _CoroutineLike[_T4],
    __coro_or_future5: _CoroutineLike[_T5],
    __coro_or_future6: _CoroutineLike[_T6],
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3, _T4, _T5, _T6]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    *coros_or_futures: _CoroutineLike[_T], return_exceptions: Literal[False] = False
) -> list[_T]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: _CoroutineLike[_T1], *, return_exceptions: bool
) -> tuple[_T1 | BaseException]:
    ...  # type: ignore[overload-overlap]


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: _CoroutineLike[_T1],
    __coro_or_future2: _CoroutineLike[_T2],
    *,
    return_exceptions: bool,
) -> tuple[_T1 | BaseException, _T2 | BaseException]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: _CoroutineLike[_T1],
    __coro_or_future2: _CoroutineLike[_T2],
    __coro_or_future3: _CoroutineLike[_T3],
    *,
    return_exceptions: bool,
) -> tuple[_T1 | BaseException, _T2 | BaseException, _T3 | BaseException]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: _CoroutineLike[_T1],
    __coro_or_future2: _CoroutineLike[_T2],
    __coro_or_future3: _CoroutineLike[_T3],
    __coro_or_future4: _CoroutineLike[_T4],
    *,
    return_exceptions: bool,
) -> tuple[
    _T1 | BaseException,
    _T2 | BaseException,
    _T3 | BaseException,
    _T4 | BaseException,
]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: _CoroutineLike[_T1],
    __coro_or_future2: _CoroutineLike[_T2],
    __coro_or_future3: _CoroutineLike[_T3],
    __coro_or_future4: _CoroutineLike[_T4],
    __coro_or_future5: _CoroutineLike[_T5],
    *,
    return_exceptions: bool,
) -> tuple[
    _T1 | BaseException,
    _T2 | BaseException,
    _T3 | BaseException,
    _T4 | BaseException,
    _T5 | BaseException,
]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: _CoroutineLike[_T1],
    __coro_or_future2: _CoroutineLike[_T2],
    __coro_or_future3: _CoroutineLike[_T3],
    __coro_or_future4: _CoroutineLike[_T4],
    __coro_or_future5: _CoroutineLike[_T5],
    __coro_or_future6: _CoroutineLike[_T6],
    *,
    return_exceptions: bool,
) -> tuple[
    _T1 | BaseException,
    _T2 | BaseException,
    _T3 | BaseException,
    _T4 | BaseException,
    _T5 | BaseException,
    _T6 | BaseException,
]:
    ...


@overload
async def gather(
    *coros_or_futures: _CoroutineLike[_T], return_exceptions: bool
) -> list[_T | BaseException]:
    ...


async def gather(  # type: ignore[misc]
    *coros: _CoroutineLike, return_exceptions: bool = False
) -> tuple:
    """A safer version of `asyncio.gather`.

    Uses a task group under the hood to not leak tasks in cases of errors
    in child tasks.

    Notable differences are:

    * `quattro.gather` only takes coroutines, and not futures.

    (See https://docs.python.org/3/library/asyncio-task.html#asyncio.gather)
    """
    if not coros:
        return ()

    subtasks = []
    async with TaskGroup() as tg:
        for coro in coros:
            subtasks.append(
                tg.create_task(coro if not return_exceptions else _wrap_coro(coro))
            )

    return tuple([await f for f in subtasks])


async def _wrap_coro(coro: Coroutine[Any, Any, _T]) -> _T | BaseException:
    """Adapt a raised exception into the return value."""
    try:
        return await coro
    except BaseException as exc:
        return exc
