"""Unit tests for the background tasks."""

from __future__ import annotations

from asyncio import CancelledError, sleep

from pytest import raises

from quattro import TaskGroup
from quattro.taskgroup import ExceptionGroup


async def forever():
    while True:
        await sleep(1)


async def error_out() -> None:
    await sleep(0.1)
    raise ValueError("Test")


async def return_result(after: float | None = None) -> int:
    if after is not None:
        await sleep(after)
    return 1


async def test_tasks_are_stopped():
    """Bg tasks are correctly stopped when exiting."""
    async with TaskGroup() as tg:
        task = tg.create_background_task(forever())

    assert task.done()


async def test_errors_interrupt():
    """Errors in bg tasks interrupt."""

    with raises(ExceptionGroup) as exc:
        async with TaskGroup() as tg:
            task = tg.create_background_task(forever())
            task2 = tg.create_background_task(error_out())
            await sleep(1)

    assert isinstance(exc.value.exceptions[0], ValueError)

    assert task.done()

    with raises(CancelledError):
        task.exception()

    assert task2.done()
    assert isinstance(task2.exception(), ValueError)


async def test_bg_cancellation():
    """Cancellations in bg tasks are swallowed.

    Apparently, task groups swallow CancelledErrors in their children.
    """

    async with TaskGroup() as tg:
        task = tg.create_task(forever())
        await sleep(1)
        task.cancel()
        await sleep(1)

    with raises(CancelledError):
        task.exception()


async def test_result():
    """Background tasks return proper results."""

    async with TaskGroup() as tg:
        task = tg.create_background_task(return_result())
        res = await task

    assert res == 1

    async with TaskGroup() as tg:
        task = tg.create_background_task(return_result(0.01))
        await sleep(0.02)
        res = await task

    assert res == 1

    async with TaskGroup() as tg:
        task = tg.create_background_task(forever())
        await sleep(0)

    if hasattr(task, "cancelling"):
        assert not task.cancelling()

    with raises(CancelledError):
        task.exception()
    with raises(CancelledError):
        task.result()
