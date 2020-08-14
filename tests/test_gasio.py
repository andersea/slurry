import trio

from gasio import Pipeline, Delay


async def test_pipeline_create(autojump_clock):
    async with Pipeline.create(None):
        await trio.sleep(1)

async def test_pipeline_passthrough(autojump_clock):
    async def produce_increasing_integers(interval, *, max=3):
        for i in range(max):
            yield i
            if i == max-1:
                break
            await trio.sleep(interval)
    
    async with Pipeline.create(produce_increasing_integers(1)) as pipeline:
        result = []
        async with pipeline.tap() as aiter:
            async for i in aiter:
                result.append(i)
        assert result == [0, 1, 2]


async def test_delay(autojump_clock):
    async def timestamp():
        yield trio.current_time()

    async with Pipeline.create(
        timestamp(),
        Delay(1)
    ) as pipeline:
        async with pipeline.tap() as aiter:
            async for item in aiter:
                assert trio.current_time() - item == 1
