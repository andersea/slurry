"""Asyncio environment for slurry."""
import asyncio
# from concurrent.futures import Future
# from queue import Queue
# from functools import partial
from threading import Thread


from typing import Any, AsyncIterable, Awaitable, Callable, Optional

import trio
from trio.lowlevel import current_trio_token

from ..sections.abc import AsyncSection


class AsyncioSection(AsyncSection):
    loop_lock = trio.Lock()
    loop = None
    trio_token = None

    async def pump(self, input: Optional[AsyncIterable[Any]], output: Callable[[Any], Awaitable[None]]):
        await self._ensure_loop()
        await self._trio_run_refine(input, output)

    async def _ensure_loop(self) -> None:
        async with self.loop_lock:
            if not self.loop:
                self.trio_token = current_trio_token()
                loop_running = trio.Event()
                loop_daemon = Thread(target=asyncio.run, args=(self._setup_asyncio_loop(loop_running),), daemon=True)
                loop_daemon.start()
                await loop_running.wait()

    async def _setup_asyncio_loop(self, loop_running):
        self.loop = asyncio.get_running_loop()
        self.trio_from_thread_run_sync(loop_running.set)
        quit = asyncio.Event()
        await quit.wait()

    async def _trio_run_refine(self, input, output):
        done = trio.Event()
        fut = asyncio.run_coroutine_threadsafe(self._asyncio_run_refine(input, output), self.loop)
        fut.add_done_callback(lambda fut: self.trio_from_thread_run_sync(done.set))
        await done.wait()

    async def _asyncio_run_refine(self, input, output):
        async def asyncio_input():
            while True:
                try:
                    yield await self.loop.run_in_executor(None, self.trio_from_thread_run, input.__anext__)
                except StopAsyncIteration:
                    break
        async def asyncio_output(item):
            await self.loop.run_in_executor(None, self.trio_from_thread_run, output, item)

        if input:
            await self.refine(asyncio_input(), asyncio_output)
        else:
            await self.refine(None, asyncio_output)

    def trio_from_thread_run(self, afn, *args):
        trio.from_thread.run(afn, *args, trio_token=self.trio_token)

    def trio_from_thread_run_sync(self, fn, *args):
        trio.from_thread.run_sync(fn, *args, trio_token=self.trio_token)
