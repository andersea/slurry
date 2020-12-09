import pytest
import trio

from slurry import Pipeline, Section, ThreadSection, Map

from .fixtures import produce_increasing_integers, SyncSquares

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

async def test_thread_section(autojump_clock):
    async with Pipeline.create(
        produce_increasing_integers(1, max=5),
        SyncSquares()
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [0, 1, 4, 9, 16]

async def test_thread_section_early_break(autojump_clock):
    async with Pipeline.create(
        produce_increasing_integers(1, max=5),
        SyncSquares()
    ) as pipeline, pipeline.tap() as aiter:
        async for i in aiter:
            if i == 4:
                break
        assert i == 4

async def test_thread_section_exception(autojump_clock):
    with pytest.raises(RuntimeError):
        async with Pipeline.create(
            produce_increasing_integers(1, max=5),
            SyncSquares(raise_after=4)
        ) as pipeline, pipeline.tap() as aiter:
                async for i in aiter:
                    pass
    assert i == 9

async def test_thread_section_section_input(autojump_clock):
    async with Pipeline.create(
        produce_increasing_integers(1),
        Map(lambda i: i),
        SyncSquares()
    ) as pipeline, pipeline.tap() as aiter:
        result = [i async for i in aiter]
        assert result == [0, 1, 4]
