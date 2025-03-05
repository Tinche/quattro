import sys
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager, AsyncExitStack
from contextvars import ContextVar
from typing import Final, TypeVar, Union, overload

if sys.version_info < (3, 10):
    from typing_extensions import Concatenate, ParamSpec
else:
    from typing import Concatenate, ParamSpec

P = ParamSpec("P")
T = TypeVar("T")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
T5 = TypeVar("T5")
T6 = TypeVar("T6")
Aw = TypeVar("Aw", bound=Awaitable)


class Deferrer(AsyncExitStack):
    """A decorator and class to enable deferring functions until the end of a coroutine.

    First, apply the Deferrer.enable decorator to a coroutine function.
    The coroutine function will receive an instance of `Deferrer` as its first
    positional argument.

    This instance of `Deferrer` can be used to enter async context managers; these
    context managers will be exited after the coroutine finishes.

    Example:
        >>> from quattro import Deferrer
        >>> @Deferrer.enable
        ... async def test(defer: Deferrer) -> None:
        ...     tg = defer(TaskGroup())  # This TaskGroup will be exited after return
        ...

    `Deferrer` is a subclass of `contextlib.AsyncExitStack`, so it supports its full
    API:

    * `AsyncExitStack.enter_async_context` (equivalent to just `Defer.__call__`
      shown above)
    * `AsyncExitStack.push_async_callback`
    * `AsyncExitStack.push_async_exit`
    * `BaseExitStack.enter_context`
    * `BaseExitStack.callback`
    * `BaseExitStack.push`

    Loosely inspired by the Go `defer` statement. (https://go.dev/tour/flowcontrol/12)
    """

    @overload
    async def __call__(self, cm: AbstractAsyncContextManager[T], /) -> T: ...

    @overload
    async def __call__(
        self,
        cm: AbstractAsyncContextManager[T],
        cm2: AbstractAsyncContextManager[T2],
        /,
    ) -> tuple[T, T2]: ...

    @overload
    async def __call__(
        self,
        cm: AbstractAsyncContextManager[T],
        cm2: AbstractAsyncContextManager[T2],
        cm3: AbstractAsyncContextManager[T3],
        /,
    ) -> tuple[T, T2, T3]: ...

    @overload
    async def __call__(
        self,
        cm: AbstractAsyncContextManager[T],
        cm2: AbstractAsyncContextManager[T2],
        cm3: AbstractAsyncContextManager[T3],
        cm4: AbstractAsyncContextManager[T4],
        /,
    ) -> tuple[T, T2, T3, T4]: ...

    @overload
    async def __call__(
        self,
        cm: AbstractAsyncContextManager[T],
        cm2: AbstractAsyncContextManager[T2],
        cm3: AbstractAsyncContextManager[T3],
        cm4: AbstractAsyncContextManager[T4],
        cm5: AbstractAsyncContextManager[T5],
        /,
    ) -> tuple[T, T2, T3, T4, T5]: ...

    @overload
    async def __call__(
        self,
        cm: AbstractAsyncContextManager[T],
        cm2: AbstractAsyncContextManager[T2],
        cm3: AbstractAsyncContextManager[T3],
        cm4: AbstractAsyncContextManager[T4],
        cm5: AbstractAsyncContextManager[T5],
        cm6: AbstractAsyncContextManager[T6],
        /,
    ) -> tuple[T, T2, T3, T4, T5, T6]: ...

    async def __call__(self, *cms):
        """A quick alias for `self.enter_async_context`.

        Enter an async context manager, and schedule its exit for later.

        Accepts multiple async context managers.
        """
        if len(cms) == 1:
            return await self.enter_async_context(cms[0])
        return tuple([await self.enter_async_context(cm) for cm in cms])

    @classmethod
    def enable(
        cls, function: "Callable[Concatenate[Deferrer, P], Aw]"
    ) -> Callable[P, Aw]:
        """A decorator to be applied to a coroutine function, enabling the use of Defer.

        The coroutine function should receive an instance of `Defer` as its first
        positional argument; this will be provided by `Defer`.
        """

        async def inner(*args, **kwargs):
            defer = cls()
            async with defer:
                return await function(defer, *args, **kwargs)

        return inner


_ACTIVE_DEFER: Final[ContextVar[Union[Deferrer, None]]] = ContextVar(
    "_ACTIVE_DEFER", default=None
)


class _defer:  # noqa: N801
    """Call to defer a context manager after applying `@defer.enable` to a coroutine
    function.
    """

    @staticmethod
    def enable(function: Callable[P, Aw]) -> Callable[P, Aw]:
        """Use as a decorator on a coroutine function to enable the use of `defer`."""

        async def inner(*args, **kwargs):
            defer = Deferrer()
            token = _ACTIVE_DEFER.set(defer)
            try:
                async with defer:
                    return await function(*args, **kwargs)
            finally:
                _ACTIVE_DEFER.reset(token)

        return inner

    @overload
    async def __call__(self, cm: AbstractAsyncContextManager[T], /) -> T: ...

    @overload
    async def __call__(
        self,
        cm: AbstractAsyncContextManager[T],
        cm2: AbstractAsyncContextManager[T2],
        /,
    ) -> tuple[T, T2]: ...

    @overload
    async def __call__(
        self,
        cm: AbstractAsyncContextManager[T],
        cm2: AbstractAsyncContextManager[T2],
        cm3: AbstractAsyncContextManager[T3],
        /,
    ) -> tuple[T, T2, T3]: ...

    @overload
    async def __call__(
        self,
        cm: AbstractAsyncContextManager[T],
        cm2: AbstractAsyncContextManager[T2],
        cm3: AbstractAsyncContextManager[T3],
        cm4: AbstractAsyncContextManager[T4],
        /,
    ) -> tuple[T, T2, T3, T4]: ...

    @overload
    async def __call__(
        self,
        cm: AbstractAsyncContextManager[T],
        cm2: AbstractAsyncContextManager[T2],
        cm3: AbstractAsyncContextManager[T3],
        cm4: AbstractAsyncContextManager[T4],
        cm5: AbstractAsyncContextManager[T5],
        /,
    ) -> tuple[T, T2, T3, T4, T5]: ...

    @overload
    async def __call__(
        self,
        cm: AbstractAsyncContextManager[T],
        cm2: AbstractAsyncContextManager[T2],
        cm3: AbstractAsyncContextManager[T3],
        cm4: AbstractAsyncContextManager[T4],
        cm5: AbstractAsyncContextManager[T5],
        cm6: AbstractAsyncContextManager[T6],
        /,
    ) -> tuple[T, T2, T3, T4, T5, T6]: ...

    async def __call__(self, *args):
        active = _ACTIVE_DEFER.get()
        if active is None:
            raise Exception(
                "Defer not enabled, did you forget to apply `@defer.enable`?"
            )
        return await active(*args)
