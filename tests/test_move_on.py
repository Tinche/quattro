from asyncio import CancelledError, create_task, sleep
from time import monotonic, time

import pytest

from quattro import move_on_after


async def test_move_on_after():
    start = time()
    t = 0.5
    with move_on_after(t) as cancel_scope:
        await sleep(1.0)

    assert cancel_scope.cancelled_caught
    assert start + t <= time() <= start + t + 0.1


async def test_move_on_after_not_triggered():
    start = time()
    with move_on_after(0.2) as cancel_scope:
        await sleep(0.1)
    assert not cancel_scope.cancelled_caught
    assert start + 0.1 <= time() <= start + 0.2
    await sleep(0.3)  # Sleep to possibly fail due to uncancelled timers


async def test_move_on_after_not_triggered_no_await():
    with move_on_after(0.2) as cancel_scope:
        pass
    assert not cancel_scope.cancelled_caught
    await sleep(0.3)


async def test_move_on_externally_cancelled():
    cancel_scope = None

    async def task():
        nonlocal cancel_scope
        with move_on_after(0.2) as cancel_scope:
            # Will be externally cancelled here.
            await sleep(1)

    t = create_task(task())
    await sleep(0.1)
    assert not t.done()
    t.cancel()
    with pytest.raises(CancelledError):
        await t

    assert cancel_scope is not None
    assert not cancel_scope.cancelled_caught


async def test_move_on_inner_exception():
    cancel_scope = None

    async def task():
        nonlocal cancel_scope
        with move_on_after(0.3) as cancel_scope:
            await sleep(0.2)
            1 / 0  # noqa: B018

    t = create_task(task())
    await sleep(0.1)
    assert not t.done()
    with pytest.raises(ZeroDivisionError):
        await t

    assert cancel_scope is not None
    assert not cancel_scope.cancelled_caught

    await sleep(0.3)  # Catch lingering timers


async def test_move_on_nested_outer_shorter():
    """Nested move_on blocks work properly."""
    checkpt_1 = 0
    checkpt_2 = 0
    start = time()
    with move_on_after(0.1) as outer:
        checkpt_1 = 1
        with move_on_after(0.2) as inner:
            checkpt_2 = 1
            await sleep(0.3)
            pytest.fail("Not cancelled")
        pytest.fail("Not cancelled")

    assert start + 0.1 <= time() <= start + 0.15
    assert checkpt_1 == 1
    assert checkpt_2 == 1
    assert outer.cancelled_caught
    assert not inner.cancelled_caught


async def test_move_on_nested_inner_shorter():
    """Nested move_on blocks work properly."""
    checkpt_1 = 0
    checkpt_2 = 0
    checkpt_3 = 0
    start = time()
    with move_on_after(0.2) as outer:
        checkpt_1 = 1
        with move_on_after(0.1) as inner:
            checkpt_2 = 1
            await sleep(0.3)
            pytest.fail("Not cancelled")
        checkpt_3 = 1
        await sleep(0.2)

    assert start + 0.2 <= time() <= start + 0.25
    assert checkpt_1 == 1
    assert checkpt_2 == 1
    assert checkpt_3 == 1
    assert outer.cancelled_caught
    assert inner.cancelled_caught


async def test_move_on_nested_happy():
    """Nested move_on blocks work properly."""
    checkpt_1 = 0
    checkpt_2 = 0
    checkpt_3 = 0
    start = monotonic()
    with move_on_after(0.2) as outer:
        checkpt_1 = 1
        with move_on_after(0.1) as inner:
            checkpt_2 = 1
        checkpt_3 = 1

    assert start <= monotonic() <= start + 0.005
    assert checkpt_1 == 1
    assert checkpt_2 == 1
    assert checkpt_3 == 1
    assert not outer.cancelled_caught
    assert not inner.cancelled_caught


async def test_move_on_cancel_myself():
    async def task():
        with move_on_after(0.5) as cancel_scope:
            await sleep(0.1)
            cancel_scope.cancel()

    t = create_task(task())
    await sleep(0.05)
    assert not t.done()
    await sleep(0.1)
    assert t.done()

    await sleep(0.5)


async def test_move_on_precancel() -> None:
    cancel_scope = move_on_after(0.5)

    async def task():
        with cancel_scope:
            await sleep(0.1)

    cancel_scope.cancel()

    t = create_task(task())
    await sleep(0.01)
    assert t.done()

    await sleep(0.5)


async def test_move_on_after_move_deadline():
    start = time()
    with move_on_after(0.1) as cancel_scope:
        await sleep(0.01)
        cancel_scope.deadline += 0.1
        await sleep(1)

    assert start + 0.2 <= time() <= start + 0.21


async def test_move_on_after_remove_deadline():
    start = time()
    with move_on_after(0.2) as cancel_scope:
        await sleep(0.1)
        cancel_scope.deadline = None
        await sleep(0.3)

    spent = time() - start
    assert 0.4 <= spent <= 0.41


async def test_move_on_after_move_deadline_to_past():
    start = time()
    with move_on_after(0.2) as cancel_scope:
        await sleep(0.1)
        cancel_scope.deadline -= 0.1
        await sleep(0.3)

    spent = time() - start
    assert 0.1 <= spent <= 0.15


async def test_enter_twice():
    """Cannot enter twice."""
    with (c := move_on_after(0.2)), pytest.raises(RuntimeError), c:
        pass
