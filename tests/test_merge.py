"""Unit tests for the merging functionality."""

from asyncio import get_running_loop, sleep

from quattro import TaskGroup, Ticker, Timer, merge, move_on_after


async def counter(num: int = 3):
    i = 0
    while i < num:
        yield i
        await sleep(0.01)
        i = i + 1


async def test_simple_merging() -> None:
    """Merging three iterators works."""

    async with TaskGroup() as tg:
        assert [x async for x in merge(tg, counter(), counter(), counter())] == [
            0,
            0,
            0,
            1,
            1,
            1,
            2,
            2,
            2,
        ]


async def test_exahaust_first() -> None:
    """Exhaust first works."""

    async with TaskGroup() as tg:
        assert [
            x
            async for x in merge(
                tg, counter(num=1), counter(), counter(), exhaust_when="first"
            )
        ] == [0, 0, 0]


async def test_exahaust_first_second_shorter() -> None:
    """Exhaust first works even when the second iterator is shorter than first."""

    async with TaskGroup() as tg:
        assert [
            x
            async for x in merge(
                tg, counter(num=2), counter(num=1), counter(), exhaust_when="first"
            )
        ] == [0, 0, 0, 1, 1]


async def test_exahaust_any() -> None:
    """Exhaust any works."""

    async with TaskGroup() as tg:
        assert [
            x
            async for x in merge(
                tg, counter(), counter(num=1), counter(), exhaust_when="any"
            )
        ] == [0, 0, 0, 1]


async def test_ticker() -> None:
    """Tickers work."""
    ticks = []
    with move_on_after(0.45):
        async for tick in Ticker(0.1):
            ticks.append(tick)

    assert ticks == [1, 2, 3, 4]


async def test_ticker_stopping() -> None:
    """Tickers can be stopped."""
    ticks = []
    ticker = Ticker(0.1)
    async for tick in ticker:
        ticks.append(tick)
        if tick == 3:
            ticker.stop()

    assert ticks == [1, 2, 3]


async def test_ticker_stopping_while_sleeping() -> None:
    """Tickers can be stopped while they're sleeping."""
    ticks = []
    ticker = Ticker(0.2)

    async def stop_it():
        await sleep(0.1)
        ticker.stop()

    async with TaskGroup() as tg:
        tg.create_background_task(stop_it())
        async for tick in ticker:
            ticks.append(tick)

    assert ticks == []


async def test_timer() -> None:
    """Timers work."""
    timer = Timer()
    results = []

    now = get_running_loop().time()
    timer.schedule_for(now + 0.1)
    timer.schedule_for(now + 0.2)

    with move_on_after(0.5):
        async for event in timer:
            results.append(event)

    assert len(results) == 2
    assert results[0].scheduled_time < results[1].scheduled_time
