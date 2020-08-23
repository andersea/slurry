from slurry import Pipeline
from slurry.combiners import Chain, Merge, Zip, ZipLatest
from slurry.producers import Repeat

from .fixtures import produce_increasing_integers, produce_alphabet

async def test_chain(autojump_clock):
    async with Pipeline.create(
        Chain(produce_increasing_integers(1, max=3), produce_alphabet(1, max=3))
    ) as pipeline, pipeline.tap() as aiter:
        result = []
        async for i in aiter:
            result.append(i)
        assert result == [0, 1, 2, 'a', 'b', 'c']

async def test_merge(autojump_clock):
    result = []
    async with Pipeline.create(
        Merge(produce_increasing_integers(1, max=3), produce_alphabet(1, max=3, delay=0.1))
    ) as pipeline, pipeline.tap() as aiter:
        async for i in aiter:
            result.append(i)
    assert result == [0, 'a', 1, 'b', 2, 'c']

async def test_merge_section(autojump_clock):
    result = []
    async with Pipeline.create(
        Merge(produce_increasing_integers(1, max=3, delay=0.5), Repeat(1, default='a'))
    ) as pipeline, pipeline.tap() as aiter:
        async for i in aiter:
            result.append(i)
            if len(result) == 6:
                break
    assert result == ['a', 0, 'a', 1, 'a', 2]


async def test_zip(autojump_clock):
    async with Pipeline.create(
        Zip(produce_increasing_integers(1), produce_alphabet(0.9))
    ) as pipeline:
        async with pipeline.tap() as aiter:
            results = []
            async for item in aiter:
                results.append(item)
            assert results == [(0,'a'), (1, 'b'), (2, 'c')]

async def test_zip_latest(autojump_clock):
    async with Pipeline.create(
        ZipLatest(
            produce_increasing_integers(1, max=3),
            produce_alphabet(1.3, max=3, delay=0.5))
    ) as pipeline, pipeline.tap() as aiter:
        result = []
        async for item in aiter:
            result.append(item)
        assert result == [(0, None),  (0, 'a'), (1, 'a'), (1, 'b'), (2, 'b')]