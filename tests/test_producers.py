import trio
from async_generator import aclosing

from slurry import Pipeline
from slurry.producers import Repeat

from .fixtures import produce_alphabet

async def test_repeat(autojump_clock):
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

                