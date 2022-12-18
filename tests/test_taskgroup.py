import asyncio
import re

from asyncio import CancelledError, create_task, get_running_loop
from gc import collect
from pickle import dumps, loads

import pytest

from quattro import taskgroup


class MyExc(Exception):
    pass


async def test_taskgroup_01() -> None:
    async def foo1() -> int:
        await asyncio.sleep(0.1)
        return 42

    async def foo2() -> int:
        await asyncio.sleep(0.2)
        return 11

    async with taskgroup.TaskGroup() as g:
        t1 = g.create_task(foo1())
        t2 = g.create_task(foo2())

    assert t1.result() == 42
    assert t2.result() == 11


async def test_taskgroup_02():
    """Taskgroups handle tasks finishing before they finish properly."""

    async def foo1():
        await asyncio.sleep(0.1)
        return 42

    async def foo2():
        await asyncio.sleep(0.2)
        return 11

    async with taskgroup.TaskGroup() as g:
        t1 = g.create_task(foo1())
        await asyncio.sleep(0.15)
        t2 = g.create_task(foo2())

    assert t1.result() == 42
    assert t2.result() == 11


async def test_taskgroup_03():
    """Task groups handle having their tasks cancelled."""

    async def foo1():
        await asyncio.sleep(1)
        return 42

    async def foo2():
        await asyncio.sleep(0.2)
        return 11

    async with taskgroup.TaskGroup() as g:
        t1 = g.create_task(foo1())
        await asyncio.sleep(0.15)
        # cancel t1 explicitly, i.e. everything should continue
        # working as expected.
        t1.cancel()

        t2 = g.create_task(foo2())

    assert t1.cancelled()
    assert t2.result() == 11


async def test_taskgroup_04():
    """Task groups propagate child exceptions and cancel their children."""

    NUM = 0
    t2_cancel = False
    t2 = None

    async def foo1():
        await asyncio.sleep(0.1)
        1 / 0

    async def foo2():
        nonlocal NUM, t2_cancel
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            t2_cancel = True
            raise
        NUM += 1

    async def runner():
        nonlocal NUM, t2

        async with taskgroup.TaskGroup() as g:
            g.create_task(foo1())
            t2 = g.create_task(foo2())

        NUM += 10

    with pytest.raises(
        taskgroup.ExceptionGroup,
        match=r"unhandled errors in a TaskGroup \(1 sub-exception\)",
    ):
        await get_running_loop().create_task(runner())

    assert NUM == 0
    assert t2_cancel
    assert t2.cancelled()


async def test_taskgroup_05():
    """Child tasks are timely cancelled if their peers error out."""

    NUM = 0
    t2_cancel = False
    runner_cancel = False

    async def foo1():
        await asyncio.sleep(0.1)
        1 / 0

    async def foo2():
        nonlocal NUM, t2_cancel
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            t2_cancel = True
            raise
        NUM += 1

    async def runner():
        nonlocal NUM, runner_cancel

        async with taskgroup.TaskGroup() as g:
            g.create_task(foo1())
            g.create_task(foo1())
            g.create_task(foo1())
            g.create_task(foo2())
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                runner_cancel = True
                raise

        NUM += 10

    # The 3 foo1 sub tasks can be racy when the host is busy - if the
    # cancellation happens in the middle, we'll see partial sub errors here
    with pytest.raises(
        taskgroup.ExceptionGroup,
        match=r"unhandled errors in a TaskGroup \((1|2|3) sub-exceptions\)",
    ):
        await create_task(runner())

    assert NUM == 0
    assert t2_cancel
    assert runner_cancel


async def test_taskgroup_06():
    """Cancelling a task waiting on exiting the TG cancels all children."""

    NUM = 0

    async def foo():
        nonlocal NUM
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            NUM += 1
            raise

    async def runner():
        async with taskgroup.TaskGroup() as g:
            for _ in range(5):
                g.create_task(foo())

    r = create_task(runner())
    await asyncio.sleep(0.1)

    assert not r.done()
    r.cancel()
    with pytest.raises(asyncio.CancelledError):
        await r

    assert NUM == 5


async def test_taskgroup_07():
    """Cancelling a task waiting inside a task group cancels the children."""

    NUM = 0

    async def foo():
        nonlocal NUM
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            NUM += 1
            raise

    async def runner():
        nonlocal NUM
        async with taskgroup.TaskGroup() as g:
            for _ in range(5):
                g.create_task(foo())

            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                NUM += 10
                raise

    r = create_task(runner())
    await asyncio.sleep(0.1)

    assert not r.done()
    r.cancel()
    with pytest.raises(asyncio.CancelledError):
        await r

    assert NUM == 15


async def test_taskgroup_cancel_propagate_child_exc() -> None:
    """Cancelling a TG propagates children exceptions."""

    async def foo() -> None:
        try:
            await asyncio.sleep(0.1)
        finally:
            1 / 0

    async def runner() -> None:
        async with taskgroup.TaskGroup() as g:
            # Spawn 5 kids, all of which will sleep.
            for _ in range(5):
                g.create_task(foo())

            # Wait for us to be cancelled.
            try:
                await asyncio.sleep(10)
            except CancelledError:
                await asyncio.sleep(0.1)
                raise

    r = create_task(runner())
    await asyncio.sleep(0.1)

    assert not r.done()
    r.cancel()
    with pytest.raises(taskgroup.ExceptionGroup) as exc:
        await r

    assert [type(e) for e in exc.value.exceptions] == [ZeroDivisionError] * 5


async def test_taskgroup_09():
    """Exceptions inside the TG async context manager cancel the children."""
    t1 = t2 = None

    async def foo1():
        await asyncio.sleep(1)
        return 42

    async def foo2():
        await asyncio.sleep(2)
        return 11

    async def runner():
        nonlocal t1, t2
        async with taskgroup.TaskGroup() as g:
            t1 = g.create_task(foo1())
            t2 = g.create_task(foo2())
            await asyncio.sleep(0.1)
            1 / 0

    try:
        await runner()
    except taskgroup.ExceptionGroup as t:
        assert {type(e) for e in t.exceptions} == {ZeroDivisionError}
    else:
        pytest.fail("TaskGroupError was not raised")

    assert t1.cancelled()
    assert t2.cancelled()


async def test_taskgroup_10():
    """Errors immediately in the TG cancel the children."""

    t1 = t2 = None

    async def foo1():
        await asyncio.sleep(1)
        return 42

    async def foo2():
        await asyncio.sleep(2)
        return 11

    async def runner():
        nonlocal t1, t2
        async with taskgroup.TaskGroup() as g:
            t1 = g.create_task(foo1())
            t2 = g.create_task(foo2())
            1 / 0

    try:
        await runner()
    except taskgroup.ExceptionGroup as t:
        assert {type(e) for e in t.exceptions} == {ZeroDivisionError}
    else:
        pytest.fail("TaskGroupError was not raised")

    assert t1.cancelled()
    assert t2.cancelled()


async def test_nested_taskgroups():
    """Nested task groups cancel properly."""

    async def foo():
        await asyncio.sleep(0.2)
        1 / 0  # This will blow up the test, should not get here.

    async def runner():
        async with taskgroup.TaskGroup():
            async with taskgroup.TaskGroup() as g2:
                for _ in range(5):
                    g2.create_task(foo())

                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    raise

    r = create_task(runner())
    await asyncio.sleep(0.1)

    assert not r.done()
    r.cancel()
    with pytest.raises(asyncio.CancelledError):
        await r


async def test_child_cancel_cancels_parent() -> None:
    """Cancellation in a child TG properly cancels children of the parent TG."""

    async def foo():
        await asyncio.sleep(0.2)
        1 / 0  # Should not get here.

    async def runner():
        async with taskgroup.TaskGroup() as g1:
            g1.create_task(foo())

            async with taskgroup.TaskGroup() as g2:
                for _ in range(5):
                    g2.create_task(foo())

                await asyncio.sleep(10)  # Await our cancellation

    r = create_task(runner())
    await asyncio.sleep(0.1)

    assert not r.done()
    r.cancel()
    with pytest.raises(asyncio.CancelledError):
        await r


async def test_taskgroup_13():
    """An error in the parent TG cancels cleanup of the child TG."""

    async def crash_after(t):
        await asyncio.sleep(t)
        raise ValueError(t)

    async def runner():
        async with taskgroup.TaskGroup() as g1:
            g1.create_task(crash_after(0.1))

            async with taskgroup.TaskGroup() as g2:
                g2.create_task(crash_after(0.2))

    r = create_task(runner())
    with pytest.raises(
        taskgroup.ExceptionGroup,
        match=r"unhandled errors in a TaskGroup \(1 sub-exception\)",
    ):
        await r


async def test_taskgroup_14():
    """An error in the child TG raises the proper exception."""

    async def crash_after(t):
        await asyncio.sleep(t)
        raise ValueError(t)

    async def runner():
        async with taskgroup.TaskGroup() as g1:
            g1.create_task(crash_after(0.2))

            async with taskgroup.TaskGroup() as g2:
                g2.create_task(crash_after(0.1))

    r = create_task(runner())
    with pytest.raises(
        taskgroup.ExceptionGroup,
        match=r"unhandled errors in a TaskGroup \(1 sub-exception\)",
    ):
        await r


async def test_errors_in_children() -> None:
    """Errors in children aren't suppressed."""

    async def crash_soon():
        await asyncio.sleep(0.3)
        1 / 0  # This will bubble out of the taskgroup.

    async def runner():
        async with taskgroup.TaskGroup() as g1:
            g1.create_task(crash_soon())
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                # Wait a little longer for the child to error out.
                await asyncio.sleep(0.5)
                raise

    r = create_task(runner())
    await asyncio.sleep(0.1)

    assert not r.done()
    r.cancel()  # Cancel before the child errors.
    with pytest.raises(taskgroup.ExceptionGroup) as exc:
        await r

    assert [type(e) for e in exc.value.exceptions] == [ZeroDivisionError]


async def test_errors_in_nested_tasks() -> None:
    """Errors in nested tasks do interfere with cancellation errors."""

    async def crash_soon():
        await asyncio.sleep(0.3)
        1 / 0

    async def nested_runner():
        async with taskgroup.TaskGroup() as g1:
            g1.create_task(crash_soon())
            try:
                await asyncio.sleep(10)  # Wait to be cancelled.
            except asyncio.CancelledError:
                await asyncio.sleep(0.5)
                raise

    async def runner():
        t = create_task(nested_runner())
        await t  # Being cancelled here will also cancel `t`

    r = create_task(runner())
    await asyncio.sleep(0.1)  # The setup.

    assert not r.done()
    r.cancel()
    with pytest.raises(taskgroup.ExceptionGroup) as exc:
        await r

    assert [type(e) for e in exc.value.exceptions] == [ZeroDivisionError]


async def test_taskgroup_17():
    """The TG main task is cancelled properly."""
    NUM = 0

    async def runner():
        nonlocal NUM
        async with taskgroup.TaskGroup():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                NUM += 10
                raise

    r = create_task(runner())
    await asyncio.sleep(0.1)

    assert not r.done()
    r.cancel()
    with pytest.raises(asyncio.CancelledError):
        await r

    assert NUM == 10


async def test_taskgroup_18():
    """Replacing CancelledError works."""
    NUM = 0

    async def runner():
        nonlocal NUM
        async with taskgroup.TaskGroup():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                NUM += 10
                # This isn't a good idea, but we have to support
                # this weird case.
                raise MyExc

    r = create_task(runner())
    await asyncio.sleep(0.1)

    assert not r.done()
    r.cancel()

    try:
        await r
    except taskgroup.ExceptionGroup as t:
        assert {type(e) for e in t.exceptions} == {MyExc}
    else:
        pytest.fail("TaskGroupError was not raised")

    assert NUM == 10


async def test_child_error_combining() -> None:
    """TaskGroupErrors combine subtask errors properly."""

    async def crash_soon():
        await asyncio.sleep(0.1)
        1 / 0

    async def nested():
        try:
            await asyncio.sleep(10)
        finally:
            raise MyExc

    async def runner():
        async with taskgroup.TaskGroup() as g:
            g.create_task(crash_soon())
            await nested()

    r = create_task(runner())
    try:
        await r
    except taskgroup.ExceptionGroup as t:
        assert {type(e) for e in t.exceptions} == {MyExc, ZeroDivisionError}
    else:
        pytest.fail("TaskGroupError was not raised")


async def test_taskgroup_20():
    """KeyboardInterrupt is handled properly."""

    async def crash_soon():
        await asyncio.sleep(0.1)
        1 / 0

    async def nested():
        try:
            await asyncio.sleep(10)
        finally:
            raise KeyboardInterrupt

    async def runner():
        async with taskgroup.TaskGroup() as g:
            g.create_task(crash_soon())
            await nested()

    with pytest.raises(KeyboardInterrupt):
        await runner()


@pytest.mark.skip(reason="Asyncio limitation")
async def test_taskgroup_21():
    # This test doesn't work as asyncio, currently, doesn't
    # know how to handle BaseExceptions.

    async def crash_soon():
        await asyncio.sleep(0.1)
        raise KeyboardInterrupt

    async def nested():
        try:
            await asyncio.sleep(10)
        finally:
            raise TypeError

    async def runner():
        async with taskgroup.TaskGroup() as g:
            g.create_task(crash_soon())
            await nested()

    with pytest.raises(KeyboardInterrupt):
        await runner()


async def test_taskgroup_22():
    """Cancellation errors are propagated properly."""

    async def foo1():
        await asyncio.sleep(1)
        return 42

    async def foo2():
        await asyncio.sleep(2)
        return 11

    async def runner():
        async with taskgroup.TaskGroup() as g:
            g.create_task(foo1())
            g.create_task(foo2())

    r = create_task(runner())
    await asyncio.sleep(0.05)
    r.cancel()

    with pytest.raises(asyncio.CancelledError):
        await r


async def test_taskgroup_23():
    """Tasks progress in the background."""
    collect()

    async def do_job(delay):
        await asyncio.sleep(delay)

    async with taskgroup.TaskGroup() as g:
        for count in range(10):
            await asyncio.sleep(0.1)
            g.create_task(do_job(0.3))
            if count == 5:
                collect()  # For PyPy
                assert len(g._tasks) < 5
        await asyncio.sleep(1.35)
        collect()  # For PyPy
        assert not len(g._tasks)


async def test_misc():
    """Test misc edge cases, for coverage."""

    async def error():
        1 / 0

    with pytest.raises(taskgroup.ExceptionGroup) as exc_info:
        g = taskgroup.TaskGroup()

        # TaskGroups cannot be used before entered.
        with pytest.raises(RuntimeError):
            temp = error()
            g.create_task(temp)

        # Clean this up for the warning.
        with pytest.raises(ZeroDivisionError):
            await temp

        async with g:
            with pytest.raises(RuntimeError):
                async with g:
                    pass

            g.create_task(asyncio.sleep(0.1))

            assert repr(g) == "<TaskGroup tasks=1 entered>"
            g.create_task(error())

            try:
                with pytest.raises(CancelledError):
                    await asyncio.sleep(0.01)
            finally:
                # On PyPy, the exception keeps the error task alive.
                assert re.match(
                    "<TaskGroup tasks=[1, 2] errors=1 cancelling>",
                    repr(g),
                )

    assert AssertionError not in {type(e) for e in exc_info.value.exceptions}
    del exc_info  # To help PyPy
    collect()  # For PyPy
    assert repr(g) == "<TaskGroup cancelling>"


async def test_taskgrouperror_pickling():
    """TaskGroupErrors pickle properly."""

    async def crash_soon():
        await asyncio.sleep(0.1)
        1 / 0

    try:
        async with taskgroup.TaskGroup() as g:
            g.create_task(crash_soon())
    except taskgroup.ExceptionGroup as t:
        assert repr(t) == repr(loads(dumps(t)))
    else:
        pytest.fail("TaskGroupError was not raised")
