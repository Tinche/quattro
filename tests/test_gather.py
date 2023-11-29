from asyncio import CancelledError, current_task, get_running_loop, sleep
from asyncio import gather as asyncio_gather

from pytest import mark, raises

from quattro import gather
from quattro.taskgroup import ExceptionGroup


@mark.parametrize("gather", [gather, asyncio_gather])
async def test_empty(gather):
    """An empty gather works."""
    # asyncio gather returns a list
    assert tuple(await gather()) == ()


@mark.parametrize("gather", [gather, asyncio_gather])
async def test_simple_gather(gather):
    """Simple gather works."""

    async def test() -> int:
        await sleep(0.01)
        return 1

    assert tuple(await gather(test(), test())) == (1, 1)


@mark.parametrize("gather", [gather, asyncio_gather])
async def test_gather_with_error(gather):
    """Gather works if there's an error."""
    cancelled = 0

    async def test() -> int:
        nonlocal cancelled
        try:
            await sleep(0.1)
        except CancelledError:
            cancelled += 1
        return 1

    async def error() -> None:
        await sleep(0.005)
        raise ValueError()

    with raises((ExceptionGroup, ValueError)) as exc_info:
        await gather(test(), test(), error())

    if gather == asyncio_gather:
        assert isinstance(exc_info.value, ValueError)
        # default asyncio behavior
        assert cancelled == 0
    else:
        assert isinstance(exc_info.value, ExceptionGroup)
        assert repr(exc_info.value.exceptions[0]) == "ValueError()"
        assert cancelled == 2


@mark.parametrize("gather", [gather, asyncio_gather])
async def test_simple_gather_exceptions(gather):
    """Simple gather works when collecting exceptions."""

    async def test() -> int:
        await sleep(0.01)
        return 1

    assert tuple(await gather(test(), test(), return_exceptions=True)) == (1, 1)


@mark.parametrize("gather", [gather, asyncio_gather])
async def test_with_error_return_excs(gather):
    """Gather works if there's an error and exceptions are returned."""

    async def test() -> int:
        await sleep(0.01)
        return 1

    err = ValueError()

    async def error() -> None:
        await sleep(0.005)
        raise err

    res = await gather(test(), test(), error(), return_exceptions=True)

    assert tuple(res) == (1, 1, err)


@mark.parametrize("gather", [gather, asyncio_gather])
async def test_parent_cancelled(gather):
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

    # We cannot use `move_on` here since asyncio.gather doesn't
    # work with it on some versions of 3.9 and 3.10.
    current = current_task()
    get_running_loop().call_later(0.001, lambda: current.cancel())

    with raises(CancelledError):
        res = await gather(test(), test())

    assert res is None
    assert cancelled == 2


@mark.parametrize("gather", [gather, asyncio_gather])
async def test_parent_cancelled_return_excs(gather):
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

    # We cannot use
    # `move_on` here since asyncio.gather doesn't
    # work with it on some versions of 3.9 and 3.10.
    current = current_task()
    get_running_loop().call_later(0.001, lambda: current.cancel())

    with raises(CancelledError):
        res = await gather(test(), test(), return_exceptions=True)

    assert res is None
    assert cancelled == 2
