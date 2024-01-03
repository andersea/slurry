import pytest
from slurry import Pipeline
from slurry.sections import Map

from .fixtures import AsyncNonIteratorIterable, SyncSquares

async def test_thread_section(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        produce_increasing_integers(1, max=5),
        SyncSquares()
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [0, 1, 4, 9, 16]

async def test_thread_section_input_non_iterator_iterable(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        AsyncNonIteratorIterable(produce_increasing_integers(1, max=5)),
        SyncSquares()
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [0, 1, 4, 9, 16]

async def test_thread_section_early_break(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        produce_increasing_integers(1, max=5),
        SyncSquares()
    ) as pipeline, pipeline.tap() as aiter:
        async for i in aiter:
            if i == 4:
                break
        assert i == 4

async def test_thread_section_exception(produce_increasing_integers, autojump_clock):
    with pytest.raises(RuntimeError):
        async with Pipeline.create(
            produce_increasing_integers(1, max=5),
            SyncSquares(raise_after=4)
        ) as pipeline, pipeline.tap() as aiter:
                async for i in aiter:
                    pass
    assert i == 9

async def test_thread_section_section_input(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        produce_increasing_integers(1),
        Map(lambda i: i),
        SyncSquares()
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [0, 1, 4]
