import trio

from gasio import create_pipeline


async def test_create_pipeline(autojump_clock):
    async with create_pipeline(None):
        await trio.sleep(1)