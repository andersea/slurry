import trio
from async_generator import aclosing

from slurry.utils import repeat

async def test_repeat(autojump_clock):
    results = []
    async with aclosing(repeat(1, 'a')) as aiter:
        start_time = trio.current_time()
        for i in range(5):
            results.append((await aiter.__anext__(), trio.current_time() - start_time))
    assert results == [('a', 0), ('a', 1), ('a', 2), ('a', 3), ('a', 4)]