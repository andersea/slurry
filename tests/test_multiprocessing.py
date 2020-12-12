
from slurry import Pipeline

from .fixtures import SimpleProcessSection, FibonacciSection

async def test_simple_process_section():
    value = 'hello, world!'

    async with Pipeline.create(SimpleProcessSection(value)) as pipeline, pipeline.tap() as aiter:
        results = [i async for i in aiter]
        assert results[0] == value

async def test_fibonacci_section():
    async with Pipeline.create(FibonacciSection(20)) as pipeline, pipeline.tap() as aiter:
        results = [i async for i in aiter]
        assert len(results) == 20
        assert results[-1] == 4181
