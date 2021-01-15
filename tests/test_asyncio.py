
import asyncio
from slurry import Pipeline
from slurry.environments import AsyncioSection

class DummyAsyncioSection(AsyncioSection):
    async def refine(self, input, output):
        pass

class SimpleAsyncioSection(AsyncioSection):
    async def refine(self, input, output):
        await output('hello, world!')
        print('Output sent')

class RepeatingAsyncioSection(AsyncioSection):

    async def refine(self, input, output):
        while True:
            await output('hello, world!')
            await asyncio.sleep(0.5)


async def test_dummy():
    async with Pipeline.create(
        DummyAsyncioSection()
    ) as pipeline, pipeline.tap() as aiter:
        async for item in aiter:
            pass

async def test_simple_section():
    async with Pipeline.create(
        SimpleAsyncioSection()
    ) as pipeline, pipeline.tap() as aiter:
        async for item in aiter:
            assert item == 'hello, world!'

async def test_early_tap_closure():
    async with Pipeline.create(
        RepeatingAsyncioSection()
    ) as pipeline, pipeline.tap() as aiter:
        async for item in aiter:
            assert item == 'hello, world!'
            break
