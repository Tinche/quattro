"""Unit tests for the background tasks."""

from asyncio import CancelledError, sleep
from typing import Never

from pytest import raises

from quattro import TaskGroup
from quattro.taskgroup import ExceptionGroup


async def forever() -> Never:
    while True:
        await sleep(1)


async def error_out() -> None:
    await sleep(0.1)
    raise ValueError("Test")


async def test_bg_tasks_are_stopped():
    """Bg tasks are correctly stopped when exiting."""
    async with TaskGroup() as tg:
        task = tg.create_background_task(forever())

    assert task.done()


async def test_bg_task_errors_interrupt():
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
