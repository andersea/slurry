import builtins
import math
from typing import Sequence, AsyncIterable

import trio
from async_generator import aclosing

from .abc import Producer, Refiner

class Zip(Producer):
    def __init__(self, *sources: Sequence[AsyncIterable]):
        super().__init__()

        self.sources = sources

    async def run(self):
        async with trio.open_nursery() as nursery:
            pull_controls = [trio.open_memory_channel(0) for _ in self.sources]
            results = [trio.open_memory_channel(0) for _ in self.sources]

            async def pull_task(source, result, pull_control):
                async with aclosing(source) as agen:
                    async for item in agen:
                        await result.send(item)
                        await pull_control.receive()
                nursery.cancel_scope.cancel()

            for i, s in builtins.enumerate(self.sources):
                nursery.start_soon(pull_task, s, results[i][0], pull_controls[i][1])
            while True:
                await self._send_output_channel.send(tuple([await r.receive() for _, r in results]))
                for p, _ in pull_controls:
                    await p.send(None)
