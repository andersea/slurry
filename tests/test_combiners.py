from slurry import Pipeline
from slurry.sections import Chain, Merge, Zip, ZipLatest, Repeat, Map, Skip

async def test_chain(produce_increasing_integers, produce_alphabet, autojump_clock):
    async with Pipeline.create(
        Chain(produce_increasing_integers(1, max=3), produce_alphabet(1, max=3))
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [0, 1, 2, 'a', 'b', 'c']

async def test_merge(produce_increasing_integers, produce_alphabet, autojump_clock):
    async with Pipeline.create(
        Merge(produce_increasing_integers(1, max=3), produce_alphabet(1, max=3, delay=0.1))
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [0, 'a', 1, 'b', 2, 'c']

async def test_merge_section(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        Merge(produce_increasing_integers(1, max=3, delay=0.5), Repeat(1, default='a'))
    ) as pipeline, pipeline.tap() as aiter:
        result = []
        async for i in aiter:
            result.append(i)
            if len(result) == 6:
                break
    assert result == ['a', 0, 'a', 1, 'a', 2]

async def test_merge_pipeline_section(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        Merge(produce_increasing_integers(1, max=3, delay=0.5),
            (
                Repeat(1, default='a'),
                Map(lambda item: item + 'x')
            ))
    ) as pipeline, pipeline.tap() as aiter:
        result = []
        async for i in aiter:
            result.append(i)
            if len(result) == 6:
                break
    assert result == ['ax', 0, 'ax', 1, 'ax', 2]

async def test_zip(produce_increasing_integers, produce_alphabet, autojump_clock):
    async with Pipeline.create(
        Zip(produce_increasing_integers(1), produce_alphabet(0.9))
    ) as pipeline:
        async with pipeline.tap() as aiter:
            results = [item async for item in aiter]
            assert results == [(0,'a'), (1, 'b'), (2, 'c')]

async def test_zip_pipeline_section(produce_increasing_integers, produce_alphabet, autojump_clock):
    async with Pipeline.create(
        Zip(
        (
            produce_increasing_integers(1, max=5),
            Skip(2)
        ),
        (
            produce_alphabet(0.9),
            Map(lambda item: item + 'x')
        ))
    ) as pipeline, pipeline.tap() as aiter:
        results = [item async for item in aiter]
        assert results == [(2,'ax'), (3, 'bx'), (4, 'cx')]

async def test_zip_latest(produce_increasing_integers, produce_alphabet, autojump_clock):
    async with Pipeline.create(
        ZipLatest(
            produce_increasing_integers(1, max=3),
            produce_alphabet(1.3, max=3, delay=0.5))
    ) as pipeline, pipeline.tap() as aiter:
        result = [item async for item in aiter]
        assert result == [(0, None),  (0, 'a'), (1, 'a'), (1, 'b'), (2, 'b')]

async def test_zip_latest_pipeline_section(produce_increasing_integers, produce_alphabet, autojump_clock):
    async with Pipeline.create(
        ZipLatest(
        (
            produce_increasing_integers(1, max=5),
            Skip(2)
            # t=2: 2
            # t=3: 3
            # t=4: 4 (Stops)
        ),
        (
            produce_alphabet(1.3, max=3, delay=0.5),
            Map(lambda item: item + 'x')
            # t=0: 'ax'
            # t=1.8: 'bx'
            # t=3.1: 'cx' (Stops)
        ))
    ) as pipeline, pipeline.tap() as aiter:
        result = [item async for item in aiter]
        assert result == [(None, 'ax'),  (None, 'bx'), (2, 'bx'), (3, 'bx'), (3, 'cx')]
