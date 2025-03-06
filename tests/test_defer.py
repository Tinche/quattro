from contextlib import asynccontextmanager, contextmanager

from pytest import raises

from quattro import Deferrer, defer


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

    @Deferrer.enable
    async def coro(defer: Deferrer, a: int) -> int:
        assert not entered
        assert await defer(asynccm()) == 1
        assert entered
        return a

    assert await coro(1) == 1

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

    @Deferrer.enable
    async def coro(defer: Deferrer) -> None:
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

    @Deferrer.enable
    async def coro(defer: Deferrer) -> None:
        assert not entered
        assert defer.enter_context(cm())
        assert entered

    await coro()

    assert exited


async def test_defer() -> None:
    """The `defer` decorator works."""

    entered = False
    exited = False

    @asynccontextmanager
    async def asynccm():
        nonlocal entered, exited
        entered = True
        yield 1
        exited = True

    @defer.enable
    async def coro(a: int) -> int:
        assert not entered
        assert await defer(asynccm()) == 1
        assert entered
        return a

    assert await coro(1) == 1

    assert exited


async def test_defer_nested() -> None:
    """The `defer` decorator works on nested coroutines."""

    entered = False
    entered2 = False
    exited = False
    exited2 = False

    @asynccontextmanager
    async def asynccm():
        nonlocal entered, exited
        entered = True
        yield 1
        exited = True

    @asynccontextmanager
    async def asynccm2():
        nonlocal entered2, exited2
        entered2 = True
        yield 2
        exited2 = True

    @defer.enable
    async def coro(a: int) -> int:
        assert not entered
        assert await defer(asynccm()) == 1
        assert entered
        return a

    @defer.enable
    async def coro2(b: int) -> int:
        assert not entered
        assert not entered2
        assert await defer(asynccm2()) == 2
        assert not entered
        assert entered2

        assert not exited
        assert not exited2

        await coro(b)

        assert exited
        assert not exited2
        return b

    assert await coro2(1) == 1

    assert exited
    assert exited2


async def test_defer_no_decorator() -> None:
    """Forgetting the decorator raises."""

    entered = False
    exited = False

    @asynccontextmanager
    async def asynccm():
        nonlocal entered, exited
        entered = True
        yield 1
        exited = True

    async def coro(a: int) -> int:
        assert not entered
        with raises(Exception) as exc:
            assert await defer(asynccm()) == 1
        raise exc.value

    with raises(Exception) as exc:
        await coro(1)

    assert "Defer not enabled" in exc.value.args[0]
