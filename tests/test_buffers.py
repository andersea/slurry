import trio

from slurry import Pipeline, FiloBuffer, Group, Delay

from .fixtures import produce_increasing_integers

async def test_filo_buffer(autojump_clock):
    async with Pipeline.create(
        FiloBuffer(3, produce_increasing_integers(1, max=5))
    ) as pipeline, pipeline.tap() as aiter:
        result = []
        async for i in aiter:
            result.append(i)
        assert result == [(0,), (0, 1), (0, 1, 2), (1, 2, 3), (2, 3, 4)]

async def test_group(autojump_clock):
    async with Pipeline.create(
        Group(2.5, produce_increasing_integers(1, max=5), max_size=3)
    ) as pipeline, pipeline.tap() as aiter:
        result = []
        async for item in aiter:
            result.append(item)
        assert result == [(0, 1, 2), (3, 4)]

async def test_delay(autojump_clock):
    async def timestamp():
        yield trio.current_time()

    async with Pipeline.create(
        Delay(1, timestamp())
    ) as pipeline, pipeline.tap() as aiter:
            async for item in aiter:
                assert trio.current_time() - item == 1