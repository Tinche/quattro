from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
)
from contextvars import ContextVar
from functools import update_wrapper, wraps
from typing import TYPE_CHECKING, Concatenate, Final, ParamSpec, TypeVar, cast, overload

if TYPE_CHECKING:
    from typing import Protocol

P = ParamSpec("P")
T = TypeVar("T")
S = TypeVar("S")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
T5 = TypeVar("T5")
T6 = TypeVar("T6")
Aw = TypeVar("Aw", bound=Awaitable)


if TYPE_CHECKING:
    S_contra = TypeVar("S_contra", contravariant=True)
    Aw_co = TypeVar("Aw_co", bound=Awaitable, covariant=True)

    class _DeferrerMethodDecorator(Protocol[S_contra, P, Aw_co]):
        @overload
        def __get__(
            self, instance: None, owner: type[S_contra], /
        ) -> Callable[Concatenate[S_contra, P], Aw_co]: ...

        @overload
        def __get__(
            self, instance: S_contra, owner: type[S_contra] | None = None, /
        ) -> Callable[P, Aw_co]: ...

        def __call__(
            self, self_: S_contra, /, *args: P.args, **kwargs: P.kwargs
        ) -> Aw_co: ...


class _DeferrerDecorator:
    def __init__(self, cls, function):
        self._cls = cls
        self._function = function
        update_wrapper(self, function)

    def __call__(self, *args, **kwargs):
        async def inner():
            defer = self._cls()
            async with defer:
                return await self._function(defer, *args, **kwargs)

        return inner()

    def __get__(self, instance, owner=None):
        bound = self._function.__get__(instance, owner)

        if instance is None:

            async def unbound(receiver, /, *args, **kwargs):
                defer = self._cls()
                async with defer:
                    return await bound(receiver, defer, *args, **kwargs)

            return cast("Callable[..., object]", wraps(bound)(unbound))

        async def inner(*args, **kwargs):
            defer = self._cls()
            async with defer:
                return await bound(defer, *args, **kwargs)

        return cast("Callable[..., object]", wraps(bound)(inner))


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
    @overload
    def enable(
        cls, function: Callable[Concatenate[Deferrer, P], Aw]
    ) -> Callable[P, Aw]: ...

    @classmethod
    @overload
    def enable(
        cls, function: Callable[Concatenate[S, Deferrer, P], Aw]
    ) -> _DeferrerMethodDecorator[S, P, Aw]: ...

    @classmethod
    def enable(cls, function):
        """A decorator to be applied to a coroutine function, enabling the use of Defer.

        The coroutine function should receive an instance of `Defer` as its first
        positional argument; this will be provided by `Defer`.
        """
        return _DeferrerDecorator(cls, function)


_ACTIVE_DEFER: Final[ContextVar[Deferrer | None]] = ContextVar(
    "_ACTIVE_DEFER", default=None
)


class _defer:  # noqa: N801
    """Call to defer a context manager after applying `@defer.enable` to a coroutine
    function.

    Also supports `defer.enter_context` for sync context managers.
    """

    @staticmethod
    def enable(function: Callable[P, Aw]) -> Callable[P, Aw]:
        """Use as a decorator on a coroutine function to enable the use of `defer`."""

        @wraps(function)
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

    def enter_context(self, cm: AbstractContextManager[T]) -> T:
        """Enter the given (sync) context manager and schedule its __exit__.

        Returns:
            The result of entering the context manager.
        """
        active = _ACTIVE_DEFER.get()
        if active is None:
            raise Exception(
                "Defer not enabled, did you forget to apply `@defer.enable`?"
            )
        return active.enter_context(cm)
