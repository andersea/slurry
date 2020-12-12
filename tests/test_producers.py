import pytest
import trio

from slurry import Pipeline
from slurry.sections import Repeat

from .fixtures import produce_alphabet

async def test_repeat_valid_args():
    with pytest.raises(RuntimeError):
        async with Pipeline.create(
            Repeat(1)
        ) as pipeline, pipeline.tap() as aiter:
            async for item in aiter:
                assert False, 'No items should be emitted due to invalid arguments provided.'

async def test_repeat_args(autojump_clock):
    results = []
    async with Pipeline.create(
        Repeat(1, 'a')
    ) as pipeline, pipeline.tap() as aiter:
        start_time = trio.current_time()
        async for item in aiter:
            results.append((item, trio.current_time() - start_time))
            if len(results) == 5:
                break
    assert results == [('a', 0), ('a', 1), ('a', 2), ('a', 3), ('a', 4)]

async def test_repeat_kwargs(autojump_clock):
    results = []
    async with Pipeline.create(
        Repeat(1, default='a')
    ) as pipeline, pipeline.tap() as aiter:
        start_time = trio.current_time()
        async for item in aiter:
            results.append((item, trio.current_time() - start_time))
            if len(results) == 5:
                break
    assert results == [('a', 0), ('a', 1), ('a', 2), ('a', 3), ('a', 4)]

async def test_repeat_input(autojump_clock):
    results = []
    async with Pipeline.create(
        produce_alphabet(1.5, max=3, delay=1),
        Repeat(1)
    ) as pipeline, pipeline.tap() as aiter:
        start_time = trio.current_time()
        async for item in aiter:
            results.append((item, trio.current_time() - start_time))
            if len(results) == 5:
                break
    assert results == [('a', 1), ('a', 2), ('b', 2.5), ('b', 3.5), ('c', 4)]

                