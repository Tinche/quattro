from asyncio import (
    CancelledError,
    TimeoutError,
    create_task,
    current_task,
    sleep,
)
from time import monotonic, time

import pytest

from quattro import CancelScope, fail_after
from quattro.cancelscope import _is_311_or_later


async def test_fail_after():
    start = time()
    t = 0.5
    with pytest.raises(TimeoutError), fail_after(t) as cancel_scope:
        await sleep(1.0)

    assert cancel_scope.cancelled_caught
    spent = time() - start
    assert t <= spent <= t + 0.01


async def test_fail_after_not_triggered():
    start = time()
    with fail_after(0.2) as cancel_scope:
        await sleep(0.1)

    spent = time() - start

    assert not cancel_scope.cancelled_caught
    assert 0.1 <= spent <= 0.15

    await sleep(0.3)  # Sleep to possibly fail due to uncancelled timers


async def test_fail_after_not_triggered_no_await():
    with fail_after(0.2) as cancel_scope:
        pass
    assert not cancel_scope.cancelled_caught
    await sleep(0.3)


async def test_fail_after_externally_cancelled() -> None:
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


async def test_fail_after_inner_exception():
    cancel_scope = None

    async def task():
        nonlocal cancel_scope
        with fail_after(0.3) as cancel_scope:
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


async def test_fail_after_nested_outer_shorter():
    """Nested fail_after blocks work properly."""
    checkpt_1 = 0
    checkpt_2 = 0
    start = time()
    with pytest.raises(TimeoutError), fail_after(0.1) as outer:
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


async def test_fail_after_nested_inner_shorter():
    """Nested fail_after blocks work properly."""
    checkpt_1 = 0
    checkpt_2 = 0
    checkpt_3 = 0
    start = time()
    with pytest.raises(TimeoutError), fail_after(0.2) as outer:
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


async def test_fail_after_nested_happy() -> None:
    """Nested fail_after blocks work properly."""
    checkpt_1 = 0
    checkpt_2 = 0
    checkpt_3 = 0
    start = monotonic()
    with fail_after(0.2) as outer:
        checkpt_1 = 1
        with fail_after(0.1) as inner:
            checkpt_2 = 1
        checkpt_3 = 1

    spent = monotonic() - start
    assert 0 <= spent <= 0.005  # Add a little buffer for PyPy
    assert checkpt_1 == 1
    assert checkpt_2 == 1
    assert checkpt_3 == 1
    assert not outer.cancelled_caught
    assert not inner.cancelled_caught


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


async def test_fail_after_precancel() -> None:
    cancel_scope = fail_after(0.5)

    async def task():
        with cancel_scope:
            await sleep(0.1)

    cancel_scope.cancel()

    t = create_task(task())
    await sleep(0.01)
    assert t.done()

    await sleep(0.5)


async def test_fail_after_move_deadline():
    start = time()
    with pytest.raises(TimeoutError), fail_after(0.1) as cancel_scope:
        await sleep(0.01)
        cancel_scope.deadline += 0.1
        await sleep(1)

    spent = time() - start

    assert 0.2 <= spent <= 0.21


async def test_fail_after_remove_deadline():
    start = time()
    with fail_after(0.2) as cancel_scope:
        await sleep(0.1)
        cancel_scope.deadline = None
        await sleep(0.3)

    spent = time() - start
    assert 0.4 <= spent <= 0.41


async def test_fail_after_move_deadline_to_past():
    start = time()
    with pytest.raises(TimeoutError), fail_after(0.2) as cancel_scope:
        await sleep(0.1)
        cancel_scope.deadline -= 0.1
        await sleep(0.3)

    spent = time() - start
    assert 0.1 <= spent <= 0.15


async def test_fail_after_move_noop():
    """Nothing bad happens if the deadline is moved by 0."""
    start = time()
    with pytest.raises(TimeoutError), fail_after(0.2) as cancel_scope:
        await sleep(0.1)
        cancel_scope.deadline += 0.0
        await sleep(0.3)

    spent = time() - start
    assert 0.2 <= spent <= 0.205

    await sleep(0.1)  # Any lingering errors


@pytest.mark.skipif(not _is_311_or_later, reason="3.11+ only")
async def test_fail_after_inner_unrelated_exc() -> None:
    """Nested scopes handle current task cancellation properly."""
    with pytest.raises(TimeoutError), CancelScope() as first:
        first._raise_on_cancel = True
        with fail_after(0.7) as second:
            try:
                with fail_after(1) as third:
                    second.cancel()
                    first.cancel()
                    raise ValueError()
            except ValueError:
                assert not third.cancelled_caught
                await sleep(0.3)
    assert not second.cancelled_caught
    assert first.cancelled_caught
    curr = current_task()
    assert curr and curr.cancelling() == 0


async def test_deadline_expired_on_enter() -> None:
    """Past deadlines work on entering the scope."""
    with pytest.raises(TimeoutError), fail_after(0):
        await sleep(1)
