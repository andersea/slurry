from slurry import Pipeline
from slurry.sections import Merge, RateLimit, Skip, SkipWhile, Filter, Changes

from .fixtures import AsyncNonIteratorIterable

async def test_skip(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        Skip(5, produce_increasing_integers(1, max=10))
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [5, 6, 7, 8, 9]

async def test_skip_input_non_iterator_iterable(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
            Skip(5, AsyncNonIteratorIterable(produce_increasing_integers(1, max=10)))
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [5, 6, 7, 8, 9]

async def test_skip_short_stream(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        Skip(5, produce_increasing_integers(1))
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == []

async def test_skipwhile(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        SkipWhile(lambda x: x < 3, produce_increasing_integers(1, max=5))
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [3, 4]

async def test_filter(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        Filter(lambda x: x%2, produce_increasing_integers(1, max=10))
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [1, 3, 5, 7, 9]

async def test_changes(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        Merge(
            produce_increasing_integers(1, max=5),
            produce_increasing_integers(1, max=5)
        ),
        Changes()
    ) as pipeline, pipeline.tap() as aiter:
            result = [i async for i in aiter]
            assert result == [0, 1, 2, 3, 4]

async def test_ratelimit(produce_mappings, autojump_clock):
    async with Pipeline.create(
        RateLimit(1, produce_mappings(0.5))
    ) as pipeline, pipeline.tap() as aiter:
        result = [item['number'] async for item in aiter]
        assert result == [0, 3, 6]

async def test_ratelimit_str_subject(produce_mappings, autojump_clock):
    async with Pipeline.create(
        RateLimit(1, produce_mappings(0.5), subject='vehicle')
    ) as pipeline, pipeline.tap() as aiter:
        result = [item['number'] async for item in aiter]
        assert result == [0,1,3,4,6,7,8]

async def test_ratelimit_callable_subject(produce_mappings, autojump_clock):
    async with Pipeline.create(
        RateLimit(1, produce_mappings(0.5), subject=lambda item: item['vehicle'][2])
    ) as pipeline, pipeline.tap() as aiter:
        result = [item['number'] async for item in aiter]
        assert result == [0,1,3,4,6,7,8]
