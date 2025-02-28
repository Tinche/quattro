import sys
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager, AsyncExitStack
from typing import TypeVar, overload

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


class Defer(AsyncExitStack):
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

        Accepts multiple async context managers.
        """
        if len(cms) == 1:
            return await self.enter_async_context(cms[0])
        return tuple([await self.enter_async_context(cm) for cm in cms])

    @classmethod
    def defer(cls, function: "Callable[Concatenate[Defer, P], Aw]"):
        async def inner(*args, **kwargs):
            defer = cls()
            async with defer:
                return await function(defer, *args, **kwargs)

        return inner
