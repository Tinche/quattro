"""Task control for asyncio."""
from __future__ import annotations

from collections.abc import Coroutine
from typing import Any, Literal, TypeVar, overload

from .taskgroup import TaskGroup

# Type hints taken from https://github.com/python/typeshed/blob/main/stdlib/asyncio/tasks.pyi,
# bless their hearts.
_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")
_T4 = TypeVar("_T4")
_T5 = TypeVar("_T5")
_T6 = TypeVar("_T6")


@overload
async def gather(  # type: ignore[overload-overlap]
    coro: Coroutine[Any, Any, _T1], *, return_exceptions: Literal[False] = False
) -> tuple[_T1]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: Coroutine[Any, Any, _T1],
    __coro_or_future2: Coroutine[Any, Any, _T2],
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: Coroutine[Any, Any, _T1],
    __coro_or_future2: Coroutine[Any, Any, _T2],
    __coro_or_future3: Coroutine[Any, Any, _T3],
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: Coroutine[Any, Any, _T1],
    __coro_or_future2: Coroutine[Any, Any, _T2],
    __coro_or_future3: Coroutine[Any, Any, _T3],
    __coro_or_future4: Coroutine[Any, Any, _T4],
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3, _T4]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: Coroutine[Any, Any, _T1],
    __coro_or_future2: Coroutine[Any, Any, _T2],
    __coro_or_future3: Coroutine[Any, Any, _T3],
    __coro_or_future4: Coroutine[Any, Any, _T4],
    __coro_or_future5: Coroutine[Any, Any, _T5],
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3, _T4, _T5]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: Coroutine[Any, Any, _T1],
    __coro_or_future2: Coroutine[Any, Any, _T2],
    __coro_or_future3: Coroutine[Any, Any, _T3],
    __coro_or_future4: Coroutine[Any, Any, _T4],
    __coro_or_future5: Coroutine[Any, Any, _T5],
    __coro_or_future6: Coroutine[Any, Any, _T6],
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3, _T4, _T5, _T6]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    *coros_or_futures: Coroutine[Any, Any, _T],
    return_exceptions: Literal[False] = False,
) -> list[_T]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: Coroutine[Any, Any, _T1], *, return_exceptions: bool
) -> tuple[_T1 | BaseException]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: Coroutine[Any, Any, _T1],
    __coro_or_future2: Coroutine[Any, Any, _T2],
    *,
    return_exceptions: bool,
) -> tuple[_T1 | BaseException, _T2 | BaseException]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: Coroutine[Any, Any, _T1],
    __coro_or_future2: Coroutine[Any, Any, _T2],
    __coro_or_future3: Coroutine[Any, Any, _T3],
    *,
    return_exceptions: bool,
) -> tuple[_T1 | BaseException, _T2 | BaseException, _T3 | BaseException]:
    ...


@overload
async def gather(  # type: ignore[overload-overlap]
    __coro_or_future1: Coroutine[Any, Any, _T1],
    __coro_or_future2: Coroutine[Any, Any, _T2],
    __coro_or_future3: Coroutine[Any, Any, _T3],
    __coro_or_future4: Coroutine[Any, Any, _T4],
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
    __coro_or_future1: Coroutine[Any, Any, _T1],
    __coro_or_future2: Coroutine[Any, Any, _T2],
    __coro_or_future3: Coroutine[Any, Any, _T3],
    __coro_or_future4: Coroutine[Any, Any, _T4],
    __coro_or_future5: Coroutine[Any, Any, _T5],
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
    __coro_or_future1: Coroutine[Any, Any, _T1],
    __coro_or_future2: Coroutine[Any, Any, _T2],
    __coro_or_future3: Coroutine[Any, Any, _T3],
    __coro_or_future4: Coroutine[Any, Any, _T4],
    __coro_or_future5: Coroutine[Any, Any, _T5],
    __coro_or_future6: Coroutine[Any, Any, _T6],
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
    *coros_or_futures: Coroutine[Any, Any, _T], return_exceptions: bool
) -> list[_T | BaseException]:
    ...


async def gather(  # type: ignore[misc]
    *coros: Coroutine, return_exceptions: bool = False
) -> tuple:
    """A safer version of `asyncio.gather`.

    Uses a task group under the hood to not leak tasks in cases of errors
    in child tasks.

    Notable differences are:

    * If a child task fails other unfinished tasks will be cancelled, just like
      in a TaskGroup.
    * `quattro.gather` only accepts coroutines and not futures and
      generators, just like a TaskGroup.
    * When `return_exceptions` is false (the default), an exception in a child task
      will cause an ExceptionGroup to bubble out of the top-level `gather()` call,
      just like in a TaskGroup.
    * Results are returned as a tuple, not a list.

    (See https://docs.python.org/3/library/asyncio-task.html#asyncio.gather)

    .. versionadded:: 23.1.0
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
