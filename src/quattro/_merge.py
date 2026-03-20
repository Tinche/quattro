from asyncio import Event as AsyncioEvent
from asyncio import Queue, get_running_loop, sleep
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable
from enum import Enum
from heapq import heappop, heappush
from typing import Any, Final, Literal, Self, TypeVar, overload

from attrs import define, field, frozen

from quattro._cancelscope import move_on_at
from quattro._taskgroup import TaskGroup


class EndOfStreamT(Enum):
    END_OF_STREAM = "END_OF_STREAM"


END_OF_STREAM: Final = EndOfStreamT.END_OF_STREAM

T = TypeVar("T")


def make_iterator(
    awaitable: Callable[[], Awaitable[T]],
    end_condition: Callable[[T], bool] | None = lambda v: v is END_OF_STREAM,
) -> AsyncGenerator[T]:
    """Convert an async function or method into an async iterator.

    The async iterator will yield elements produced by the provided awaitable
    until the `end_sentinel` is produced, at which point the iterator will
    be exhausted. By default, the end sentinel is `END_OF_STREAM`.
    """

    if end_condition is not None:

        async def generator() -> AsyncGenerator[T]:
            while True:
                element = await awaitable()
                if end_condition(element):
                    return
                yield element

    else:

        async def generator() -> AsyncGenerator[T]:
            while True:
                yield await awaitable()

    return generator()


@define
class Ticker:
    """This class is an async iterator.

    It yields a monotonically increasing integer, starting with 1, every `period`
    seconds.

    `Ticker.stop()` stops any further yields.
    """

    _period: float
    _state: tuple[float, int] | Literal["not_started", "stopped"] = field(
        default="not_started", init=False
    )

    def stop(self) -> None:
        """Stop yielding ticks from this instant forward.

        If an iteration step is already in progress, iteration will stop after
        it elapses.
        """
        self._state = "stopped"

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> int:
        if self._state == "stopped":
            raise StopAsyncIteration

        if self._state == "not_started":
            res = 1
            start = get_running_loop().time()
        else:
            start, res = self._state
            res += 1

        self._state = (start, res)

        await sleep(start + (res * self._period) - get_running_loop().time())

        if self._state == "stopped":
            # Maybe got cancelled in the meantime.
            raise StopAsyncIteration

        return res


@define
class Timer:
    """An async iterator that can yield scheduled events."""

    _closest_event: AsyncioEvent = field(init=False, factory=AsyncioEvent)
    _scheduled_events: list[float] = field(factory=list, init=False)

    @frozen
    class Event:
        """Event triggered at a scheduled time."""

        scheduled_time: float

    def schedule_for(self, time: float) -> None:
        """Schedule an event for the specified time."""
        heappush(self._scheduled_events, time)
        self._closest_event.set()

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> Event:
        while True:
            if not self._scheduled_events:
                self._closest_event.clear()
                await self._closest_event.wait()
                continue

            now = get_running_loop().time()
            next_time = self._scheduled_events[0]  # Peek at earliest time

            if next_time <= now:
                scheduled_time = heappop(
                    self._scheduled_events
                )  # Remove the earliest time
                return self.Event(scheduled_time)

            # Wait until the next scheduled time or until a new event is scheduled
            self._closest_event.clear()

            # Use quattro.move_on_at to wait until the next scheduled time
            with move_on_at(next_time):
                await self._closest_event.wait()
                # If we get here, a new event was scheduled
                # Continue the loop to check if it should be processed now


A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")
E = TypeVar("E")
F = TypeVar("F")


@overload
def merge(
    tg: TaskGroup,
    __first: AsyncIterator[A],
    __second: AsyncIterator[B],
    /,
    *,
    exhaust_when: Literal["all", "first", "any"] = "all",
) -> AsyncIterator[A | B]: ...


@overload
def merge(
    tg: TaskGroup,
    __first: AsyncIterator[A],
    __second: AsyncIterator[B],
    __third: AsyncIterator[C],
    /,
    *,
    exhaust_when: Literal["all", "first", "any"] = "all",
) -> AsyncIterator[A | B | C]: ...


@overload
def merge(
    tg: TaskGroup,
    __first: AsyncIterator[A],
    __second: AsyncIterator[B],
    __third: AsyncIterator[C],
    __fourth: AsyncIterator[D],
    /,
    *,
    exhaust_when: Literal["all", "first", "any"] = "all",
) -> AsyncIterator[A | B | C | D]: ...


@overload
def merge(
    tg: TaskGroup,
    __first: AsyncIterator[A],
    __second: AsyncIterator[B],
    __third: AsyncIterator[C],
    __fourth: AsyncIterator[D],
    __fifth: AsyncIterator[E],
    /,
    *,
    exhaust_when: Literal["all", "first", "any"] = "all",
) -> AsyncIterator[A | B | C | D | E]: ...


@overload
def merge(
    tg: TaskGroup,
    __first: AsyncIterator[A],
    __second: AsyncIterator[B],
    __third: AsyncIterator[C],
    __fourth: AsyncIterator[D],
    __fifth: AsyncIterator[E],
    __sixth: AsyncIterator[F],
    /,
    *,
    exhaust_when: Literal["all", "first", "any"] = "all",
) -> AsyncIterator[A | B | C | D | E | F]: ...


def merge(
    tg: TaskGroup,
    __first: AsyncIterator,
    __second: AsyncIterator,
    /,
    *rest: AsyncIterator,
    exhaust_when: Literal["all", "first", "any"] = "all",
) -> AsyncIterator:
    """Merge source iterators into one, yielding a union of all results.

    The resulting iterator will continue until:
    * `exhaust_when` is `all`: all the iterators are exhausted
    * `exhaust_when` is `first`: the first iterator is exhausted
    * `exhaust_when` is `any`: any of the given iterators is exhausted

    If any source iterator raises an exception, the exception will be wrapped in an
    ExceptionGroup and raised. The resulting iterator will become invalid.
    """
    join_queue: Queue = Queue()

    if exhaust_when == "first":

        async def pump_first(
            iterable: AsyncIterator, sink: Callable[[Any], Awaitable] = join_queue.put
        ) -> None:
            async for val in iterable:
                await sink(val)
            await sink(END_OF_STREAM)

        async def pump(
            iterable: AsyncIterator, sink: Callable[[Any], Awaitable] = join_queue.put
        ) -> None:
            async for val in iterable:
                await sink(val)

        tg.create_background_task(pump_first(__first))
    else:
        if exhaust_when == "all":
            remaining = len(rest) + 2
        elif exhaust_when == "any":
            remaining = 1

        async def pump(
            iterable: AsyncIterator, sink: Callable[[Any], Awaitable] = join_queue.put
        ) -> None:
            async for val in iterable:
                await sink(val)
            nonlocal remaining
            remaining -= 1
            if remaining == 0:
                await sink(END_OF_STREAM)

        tg.create_background_task(pump(__first))

    tg.create_background_task(pump(__second))
    for r in rest:
        tg.create_background_task(pump(r))

    return make_iterator(join_queue.get)
