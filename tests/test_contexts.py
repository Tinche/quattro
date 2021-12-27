import sys

from asyncio import TimeoutError, get_running_loop, sleep

import pytest

from quattro import (
    TaskGroup,
    fail_at,
    get_current_effective_deadline,
    move_on_at,
)


@pytest.mark.asyncio
async def test_effective_deadline():
    assert get_current_effective_deadline() == float("inf")

    deadline = get_running_loop().time() + 10
    with move_on_at(deadline):
        assert get_current_effective_deadline() == deadline

    assert get_current_effective_deadline() == float("inf")


@pytest.mark.asyncio
async def test_nested_deadlines():
    assert get_current_effective_deadline() == float("inf")

    deadline = get_running_loop().time() + 10
    with move_on_at(deadline):
        assert get_current_effective_deadline() == deadline

        fail_deadline = deadline - 5
        with fail_at(fail_deadline):
            assert get_current_effective_deadline() == fail_deadline

        assert get_current_effective_deadline() == deadline

        future_deadline = deadline + 5
        with move_on_at(future_deadline):
            assert get_current_effective_deadline() == deadline

    assert get_current_effective_deadline() == float("inf")


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
@pytest.mark.asyncio
async def test_nested_deadlines_error():
    assert get_current_effective_deadline() == float("inf")

    deadline = get_running_loop().time() + 1
    with move_on_at(deadline):
        assert get_current_effective_deadline() == deadline

        fail_deadline = deadline - 0.7
        with pytest.raises(TimeoutError):
            with fail_at(fail_deadline):
                assert get_current_effective_deadline() == fail_deadline
                await sleep(1.0)

        assert get_current_effective_deadline() == deadline

        future_deadline = deadline + 1
        with move_on_at(future_deadline):
            assert get_current_effective_deadline() == deadline

    assert get_current_effective_deadline() == float("inf")


@pytest.mark.asyncio
async def test_moved_nested_deadlines():
    assert get_current_effective_deadline() == float("inf")

    deadline = get_running_loop().time() + 10

    with move_on_at(deadline) as cancel_scope:
        assert get_current_effective_deadline() == deadline

        new_deadline = deadline + 1
        cancel_scope.deadline = new_deadline
        assert get_current_effective_deadline() == new_deadline

        fail_deadline = deadline - 5
        with fail_at(fail_deadline):
            assert get_current_effective_deadline() == fail_deadline

        assert get_current_effective_deadline() == new_deadline

        future_deadline = deadline + 5
        with move_on_at(future_deadline):
            assert get_current_effective_deadline() == new_deadline

        cancel_scope.deadline = None
        assert get_current_effective_deadline() == float("inf")

    assert get_current_effective_deadline() == float("inf")


@pytest.mark.asyncio
async def test_taskgroup_deadlines():
    assert get_current_effective_deadline() == float("inf")

    async with TaskGroup() as tg:

        async def task():
            assert get_current_effective_deadline() == float("inf")

        await tg.create_task(task())

    deadline = get_running_loop().time() + 1

    with move_on_at(deadline):
        assert get_current_effective_deadline() == deadline
        async with TaskGroup() as tg:

            async def task():
                assert get_current_effective_deadline() == deadline

                new_deadline = deadline - 0.1
                with move_on_at(new_deadline):
                    assert get_current_effective_deadline() == new_deadline

                assert get_current_effective_deadline() == deadline

            await tg.create_task(task())
