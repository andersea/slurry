import trio

from slurry import Pipeline
from slurry.sections.abc import Section

from .fixtures import produce_increasing_integers

async def test_pipeline_create(autojump_clock):
    async with Pipeline.create(None):
        await trio.sleep(1)

async def test_pipeline_passthrough(autojump_clock):
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
    class Spammer(Section):
        def __init__(self, stop) -> None:
            self.stop = stop

        async def pump(self, input, output):
            for i in range(self.stop):
                await output.send(i)

    for _ in range(100):
        async with Pipeline.create(
            Spammer(10),
        ) as pipeline, pipeline.tap() as aiter:
            async for i in aiter:
                assert isinstance(i, int)
                break
