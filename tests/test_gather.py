from asyncio import CancelledError, sleep

from pytest import raises

from quattro import gather, move_on_after


async def test_simple_gather():
    """Simple gather works."""

    async def test() -> int:
        await sleep(0.01)
        return 1

    assert await gather(test(), test()) == (1, 1)


async def test_gather_with_error():
    """Gather works if there's an error."""
    cancelled = 0

    async def test() -> int:
        nonlocal cancelled
        try:
            await sleep(0.01)
        except CancelledError:
            cancelled += 1
        return 1

    async def error() -> None:
        await sleep(0.005)
        raise ValueError()

    with raises(ExceptionGroup) as exc_info:
        await gather(test(), test(), error())

    assert repr(exc_info.value.exceptions[0]) == "ValueError()"


async def test_simple_gather_exceptions():
    """Simple gather works when collecting exceptions."""

    async def test() -> int:
        await sleep(0.01)
        return 1

    assert await gather(test(), test(), return_exceptions=True) == (1, 1)


async def test_with_error_return_excs():
    """Gather works if there's an error and exceptions are returned."""

    async def test() -> int:
        await sleep(0.01)
        return 1

    err = ValueError()

    async def error() -> None:
        await sleep(0.005)
        raise err

    res = await gather(test(), test(), error(), return_exceptions=True)

    assert res == (1, 1, err)


async def test_parent_cancelled():
    """When the parent is cancelled, the children are also cancelled."""
    cancelled = 0

    async def test() -> int:
        nonlocal cancelled
        try:
            await sleep(0.01)
        except CancelledError:
            cancelled += 1
            raise
        return 1

    res = None

    with move_on_after(0.001):
        res = await gather(test(), test())

    assert res is None
    assert cancelled == 2


async def test_parent_cancelled_return_excs():
    """When the parent is cancelled, the children are also cancelled."""
    cancelled = 0

    async def test() -> int:
        nonlocal cancelled
        try:
            await sleep(0.01)
        except CancelledError:
            cancelled += 1
            raise
        return 1

    res = None

    with move_on_after(0.001):
        res = await gather(test(), test(), return_exceptions=True)

    assert res is None
    assert cancelled == 2
