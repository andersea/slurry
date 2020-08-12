import builtins
import math
from typing import Sequence, AsyncIterable

import trio
from async_generator import aclosing

from .abc import Producer, Refiner

class Extension(Producer):
    def __init__(self, output):
        self._output = output
    
    async def run(self):
        pass


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

class Delay(Refiner):
    def __init__(self, interval: float):
        super().__init__()
        self.interval = interval
    
    async def run(self):
        buffer_input_channel, buffer_output_channel = trio.open_memory_channel(math.inf)

        async def pull_task():
            async with self._input:
                async for item in self._input:
                    await buffer_input_channel.send((item, trio.current_time() + self.interval))
        
        async def push_task():
            async with buffer_output_channel:
                async for item, timestamp in buffer_output_channel:
                    now = trio.current_time()
                    if timestamp > now:
                        await trio.sleep(timestamp - now)
                    await self._send_output_channel.send(item)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(pull_task)
            nursery.start_soon(push_task)