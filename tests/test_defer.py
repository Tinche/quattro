from contextlib import asynccontextmanager, contextmanager

from quattro import Defer


async def test_defer_async() -> None:
    """Async defer works."""

    entered = False
    exited = False

    @asynccontextmanager
    async def asynccm():
        nonlocal entered, exited
        entered = True
        yield 1
        exited = True

    @Defer.defer
    async def coro(defer: Defer) -> None:
        assert not entered
        assert await defer(asynccm()) == 1
        assert entered

    await coro()

    assert exited


async def test_defer_async_several() -> None:
    """Async defer works with multiple contexts."""

    entered = [False, False]
    exited = [False, False]

    @asynccontextmanager
    async def asynccm():
        nonlocal entered, exited
        entered[0] = True
        yield 1
        exited[0] = True

    @asynccontextmanager
    async def asynccm2():
        nonlocal entered, exited
        entered[1] = True
        yield 2
        exited[1] = True

    @Defer.defer
    async def coro(defer: Defer) -> None:
        assert not entered[0]
        assert not entered[1]
        assert await defer(asynccm(), asynccm2()) == (1, 2)
        assert entered[0]
        assert entered[1]

    await coro()

    assert exited[0]
    assert exited[1]


async def test_defer_sync_in_async() -> None:
    """Sync defer in coroutines works."""

    entered = False
    exited = False

    @contextmanager
    def cm():
        nonlocal entered, exited
        entered = True
        yield 1
        exited = True

    @Defer.defer
    async def coro(defer: Defer) -> None:
        assert not entered
        assert defer.enter_context(cm())
        assert entered

    await coro()

    assert exited
