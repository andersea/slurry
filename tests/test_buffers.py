import trio

from slurry import Pipeline, Window, Group, Delay

from .fixtures import produce_increasing_integers, spam_wait_spam_integers

async def test_window(autojump_clock):
    async with Pipeline.create(
        Window(3, produce_increasing_integers(1, max=5))
    ) as pipeline, pipeline.tap() as aiter:
        result = [item async for item in aiter]
        assert result == [(0,), (0, 1), (0, 1, 2), (1, 2, 3), (2, 3, 4)]

async def test_group_max_size(autojump_clock):
    async with Pipeline.create(
        Group(2.5, produce_increasing_integers(1, max=5), max_size=3)
    ) as pipeline, pipeline.tap() as aiter:
        result = [item async for item in aiter]
        assert result == [(0, 1, 2), (3, 4)]

async def test_group_timeout(autojump_clock):
    async with Pipeline.create(
        Group(2.5, spam_wait_spam_integers(5))
    ) as pipeline, pipeline.tap() as aiter:
        result = [item async for item in aiter]
        assert result == [(0, 1, 2, 3, 4), (0, 1, 2, 3, 4)]

async def test_delay(autojump_clock):
    async def timestamp():
        yield trio.current_time()

    async with Pipeline.create(
        Delay(1, timestamp())
    ) as pipeline, pipeline.tap() as aiter:
            async for item in aiter:
                assert trio.current_time() - item == 1