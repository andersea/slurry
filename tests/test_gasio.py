import trio

from gasio import Pipeline, Delay


async def test_pipeline_create(autojump_clock):
    async with Pipeline.create(None):
        await trio.sleep(1)

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
