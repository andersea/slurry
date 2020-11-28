from slurry import Pipeline
from slurry.combiners import Merge
from slurry.filters import RateLimit, Skip, Filter, Changes

from .fixtures import produce_increasing_integers, produce_mappings

async def test_skip(autojump_clock):
    async with Pipeline.create(
        Skip(5, produce_increasing_integers(1, max=10))
    ) as pipeline, pipeline.tap() as aiter:
        result = []
        async for i in aiter:
            result.append(i)
        assert result == [5, 6, 7, 8, 9]

async def test_filter(autojump_clock):
    async with Pipeline.create(
        Filter(lambda x: x%2, produce_increasing_integers(1, max=10))
    ) as pipeline, pipeline.tap() as aiter:
        result = []
        async for i in aiter:
            result.append(i)
        assert result == [1, 3, 5, 7, 9]

async def test_changes(autojump_clock):
    async with Pipeline.create(
        Merge(
            produce_increasing_integers(1, max=5),
            produce_increasing_integers(1, max=5)
        ),
        Changes()
    ) as pipeline, pipeline.tap() as aiter:
            result = []
            async for i in aiter:
                result.append(i)
            assert result == [0, 1, 2, 3, 4]

async def test_ratelimit(autojump_clock):
    async with Pipeline.create(
        RateLimit(1, produce_mappings(0.5))
    ) as pipeline, pipeline.tap() as aiter:
        result = [item['number'] async for item in aiter]
        assert result == [0, 3, 6]

async def test_ratelimit_str_subject(autojump_clock):
    async with Pipeline.create(
        RateLimit(1, produce_mappings(0.5), subject='vehicle')
    ) as pipeline, pipeline.tap() as aiter:
        result = [item['number'] async for item in aiter]
        assert result == [0,1,3,4,6,7,8]

async def test_ratelimit_callable_subject(autojump_clock):
    async with Pipeline.create(
        RateLimit(1, produce_mappings(0.5), subject=lambda item: item['vehicle'][2])
    ) as pipeline, pipeline.tap() as aiter:
        result = [item['number'] async for item in aiter]
        assert result == [0,1,3,4,6,7,8]
