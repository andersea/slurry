from slurry import Pipeline
from slurry.refiners import Map

from .fixtures import produce_increasing_integers

async def test_map(autojump_clock):
    async with Pipeline.create(
        Map(lambda x: x*x, produce_increasing_integers(1, max=5))
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [0, 1, 4, 9, 16]
