from slurry import Pipeline
from slurry.sections import Map, Delay
import trio

from .fixtures import produce_increasing_integers

async def test_map(autojump_clock):
    async with Pipeline.create(
        Map(lambda x: x*x, produce_increasing_integers(1, max=5))
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [0, 1, 4, 9, 16]

async def test_map_section(autojump_clock):
    async with Pipeline.create(
        Map(lambda x: x*x, Delay(1, produce_increasing_integers(1, max=5)))
    ) as pipeline, pipeline.tap() as aiter:
        result = [(i, trio.current_time()) async for i in aiter]
        assert result == [(0, 1), (1, 2), (4, 3), (9, 4), (16, 5)]
