import pytest
import trio

from slurry import Pipeline
from slurry.sections import Map
from slurry.environments import TrioSection

async def test_pipeline_create(autojump_clock):
    async with Pipeline.create(None):
        await trio.sleep(1)

async def test_pipeline_passthrough(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(produce_increasing_integers(1)) as pipeline:
        async with pipeline.tap() as aiter:
            result = [i async for i in aiter]
            assert result == [0, 1, 2]

async def test_early_tap_closure_aiter(autojump_clock):
    async def spammer(stop):
        for i in range(stop):
            yield i

    for _ in range(100):
        async with Pipeline.create(
            spammer(10),
        ) as pipeline, pipeline.tap() as aiter:
            async for i in aiter:
                assert isinstance(i, int)
                break

async def test_early_tap_closure_section(autojump_clock):
    class Spammer(TrioSection):
        def __init__(self, stop) -> None:
            self.stop = stop

        async def refine(self, input, output):
            for i in range(self.stop):
                await output(i)

    for _ in range(100):
        async with Pipeline.create(
            Spammer(10),
        ) as pipeline, pipeline.tap() as aiter:
            async for i in aiter:
                assert isinstance(i, int)
                break

async def test_welding(produce_increasing_integers, autojump_clock):
    async with Pipeline.create(
        produce_increasing_integers(1),
        (Map(lambda i: i + 1),)
    ) as pipeline:
        async with pipeline.tap() as aiter:
            result = [i async for i in aiter]
            assert result == [1, 2, 3]

async def test_welding_two_generator_functions_not_allowed(produce_increasing_integers, autojump_clock):
    with pytest.raises(ValueError):
        async with Pipeline.create(
            produce_increasing_integers(1),
            produce_increasing_integers(1),
        ) as pipeline, pipeline.tap() as aiter:
            result = [i async for i in aiter]
