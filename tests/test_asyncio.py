
import asyncio

import pytest
from slurry import Pipeline
from slurry.environments import AsyncioSection

from .fixtures import produce_increasing_integers


class DummyAsyncioSection(AsyncioSection):
    async def refine(self, input, output):
        pass

class SimpleAsyncioSection(AsyncioSection):
    async def refine(self, input, output):
        await output('hello, world!')

class BadAsyncioSection(AsyncioSection):
    async def refine(self, input, output):
        raise RuntimeError('RuntimeError')

class RepeatingAsyncioSection(AsyncioSection):

    async def refine(self, input, output):
        while True:
            await output('hello, world!')
            await asyncio.sleep(0.5)

class SquaresAsyncioSection(AsyncioSection):
    async def refine(self, input, output):
        async for i in input:
            await output(i*i)

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

async def test_bad_section():
    with pytest.raises(RuntimeError):
        async with Pipeline.create(
            BadAsyncioSection()
        ) as pipeline, pipeline.tap() as aiter:
            results = [item async for item in aiter]

async def test_early_tap_closure():
    async with Pipeline.create(
        RepeatingAsyncioSection()
    ) as pipeline, pipeline.tap() as aiter:
        async for item in aiter:
            assert item == 'hello, world!'
            break

async def test_trio_generator_to_asyncio(autojump_clock):
    async with Pipeline.create(
        produce_increasing_integers(1),
        SquaresAsyncioSection()
    ) as pipeline, pipeline.tap() as aiter:
        results = [i async for i in aiter]
        assert results == [0, 1, 4]

async def test_spam_pipelines(autojump_clock):
    for _ in range(100):
        async with Pipeline.create(
            produce_increasing_integers(1),
            SquaresAsyncioSection()
        ) as pipeline, pipeline.tap() as aiter:
            results = [i async for i in aiter]
            assert results == [0, 1, 4]
