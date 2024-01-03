import pytest
import trio

from slurry import Pipeline
from slurry.sections import Repeat, Metronome, InsertValue

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

async def test_metronome():
    async with Pipeline.create(
        produce_alphabet(5, max=3),
        Metronome(5)
    ) as pipeline, pipeline.tap() as aiter:
        results = []
        start_time = trio.current_time()
        async for item in aiter:
            results.append((item, trio.current_time() - start_time))
            if len(results) == 2:
                break
    assert [x[0] for x in results] == ['a', 'b']
    assert 5 - results[1][1] + results[0][1] < 0.1

async def test_insert_value(autojump_clock):
    async with Pipeline.create(
        produce_alphabet(1, max=3, delay=1),
        InsertValue('n')
    ) as pipeline, pipeline.tap() as aiter:
        start_time = trio.current_time()
        results = [(v, trio.current_time() - start_time) async for v in aiter]
        assert results == [('n', 0), ('a', 1), ('b', 2), ('c', 3)]

async def test_insert_value_no_input(autojump_clock):
    async with Pipeline.create(
            InsertValue('n')
    ) as pipeline, pipeline.tap() as aiter:
        results = [v async for v in aiter]
        assert results == ['n']
