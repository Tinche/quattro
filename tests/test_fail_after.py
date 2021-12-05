import sys

from asyncio import CancelledError, TimeoutError, create_task, sleep
from time import time

import pytest

from quattro import fail_after


pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 9), reason="requires python3.9 or higher"
)


@pytest.mark.asyncio
async def test_fail_after():
    start = time()
    t = 0.5
    with pytest.raises(TimeoutError):
        with fail_after(t) as cancel_scope:
            await sleep(1.0)

    assert cancel_scope.cancelled_caught
    spent = time() - start
    assert t <= spent <= t + 0.01


@pytest.mark.asyncio
async def test_fail_after_not_triggered():
    start = time()
    with fail_after(0.2) as cancel_scope:
        await sleep(0.1)

    spent = time() - start

    assert not cancel_scope.cancelled_caught
    assert 0.1 <= spent <= 0.15

    await sleep(0.3)  # Sleep to possibly fail due to uncancelled timers


@pytest.mark.asyncio
async def test_fail_after_not_triggered_no_await():
    with fail_after(0.2) as cancel_scope:
        pass
    assert not cancel_scope.cancelled_caught
    await sleep(0.3)


@pytest.mark.asyncio
async def test_fail_after_externally_cancelled():
    cancel_scope = None

    async def task():
        nonlocal cancel_scope
        with fail_after(0.2) as cancel_scope:
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


@pytest.mark.asyncio
async def test_fail_after_inner_exception():
    cancel_scope = None

    async def task():
        nonlocal cancel_scope
        with fail_after(0.3) as cancel_scope:
            await sleep(0.2)
            1 / 0

    t = create_task(task())
    await sleep(0.1)
    assert not t.done()
    with pytest.raises(ZeroDivisionError):
        await t

    assert cancel_scope is not None
    assert not cancel_scope.cancelled_caught

    await sleep(0.3)  # Catch lingering timers


@pytest.mark.asyncio
async def test_fail_after_nested_outer_shorter():
    """Nested fail_after blocks work properly."""
    checkpt_1 = 0
    checkpt_2 = 0
    start = time()
    with pytest.raises(TimeoutError):
        with fail_after(0.1) as outer:
            checkpt_1 = 1
            with fail_after(0.2) as inner:
                checkpt_2 = 1
                await sleep(0.3)
                pytest.fail("Not cancelled")
            pytest.fail("Not cancelled")

    spent = time() - start
    assert 0.1 <= spent <= 0.15
    assert checkpt_1 == 1
    assert checkpt_2 == 1
    assert outer.cancelled_caught
    assert not inner.cancelled_caught


@pytest.mark.asyncio
async def test_fail_after_nested_inner_shorter():
    """Nested fail_after blocks work properly."""
    checkpt_1 = 0
    checkpt_2 = 0
    checkpt_3 = 0
    start = time()
    with pytest.raises(TimeoutError):
        with fail_after(0.2) as outer:
            checkpt_1 = 1
            try:
                with fail_after(0.1) as inner:
                    checkpt_2 = 1
                    await sleep(0.3)
                    pytest.fail("Not cancelled")
            except TimeoutError:
                checkpt_3 = 1
                await sleep(0.2)
            else:
                pytest.fail("No timeout")

    spent = time() - start

    assert 0.2 <= spent <= 0.25
    assert checkpt_1 == 1
    assert checkpt_2 == 1
    assert checkpt_3 == 1
    assert outer.cancelled_caught
    assert inner.cancelled_caught


@pytest.mark.asyncio
async def test_fail_after_nested_happy():
    """Nested fail_after blocks work properly."""
    checkpt_1 = 0
    checkpt_2 = 0
    checkpt_3 = 0
    start = time()
    with fail_after(0.2) as outer:
        checkpt_1 = 1
        with fail_after(0.1) as inner:
            checkpt_2 = 1
        checkpt_3 = 1

    spent = time() - start
    assert 0 <= spent <= 0.002
    assert checkpt_1 == 1
    assert checkpt_2 == 1
    assert checkpt_3 == 1
    assert not outer.cancelled_caught
    assert not inner.cancelled_caught


@pytest.mark.asyncio
async def test_fail_after_cancel_myself():
    async def task():
        with fail_after(0.5) as cancel_scope:
            await sleep(0.1)
            cancel_scope.cancel()

    t = create_task(task())
    await sleep(0.05)
    assert not t.done()
    await sleep(0.1)
    assert t.done()

    with pytest.raises(CancelledError):
        await t

    await sleep(0.5)


@pytest.mark.skip(reason="Not implemented yet")
@pytest.mark.asyncio
async def test_fail_after_precancel():
    cancel_scope = fail_after(0.5)

    async def task():
        with cancel_scope:
            await sleep(0.1)

    cancel_scope.cancel()

    t = create_task(task())
    await sleep(0.01)
    assert t.done()

    await sleep(0.5)


@pytest.mark.asyncio
async def test_fail_after_move_deadline():
    start = time()
    with pytest.raises(TimeoutError):
        with fail_after(0.1) as cancel_scope:
            await sleep(0.01)
            cancel_scope.deadline += 0.1
            await sleep(1)

    spent = time() - start

    assert 0.2 <= spent <= 0.21


@pytest.mark.asyncio
async def test_fail_after_remove_deadline():
    start = time()
    with fail_after(0.2) as cancel_scope:
        await sleep(0.1)
        cancel_scope.deadline = None
        await sleep(0.3)

    spent = time() - start
    assert 0.4 <= spent <= 0.41


@pytest.mark.asyncio
async def test_fail_after_move_deadline_to_past():
    start = time()
    with pytest.raises(TimeoutError):
        with fail_after(0.2) as cancel_scope:
            await sleep(0.1)
            cancel_scope.deadline -= 0.1
            await sleep(0.3)

    spent = time() - start
    assert 0.1 <= spent <= 0.15


@pytest.mark.asyncio
async def test_fail_after_move_noop():
    """Nothing bad happens if the deadline is moved by 0."""
    start = time()
    with pytest.raises(TimeoutError):
        with fail_after(0.2) as cancel_scope:
            await sleep(0.1)
            cancel_scope.deadline += 0.0
            await sleep(0.3)

    spent = time() - start
    assert 0.2 <= spent <= 0.205

    await sleep(0.1)  # Any lingering errors
