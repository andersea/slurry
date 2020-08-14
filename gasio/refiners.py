import math

import trio
from async_generator import aclosing

from .abc import Refiner

class Delay(Refiner):
    def __init__(self, interval: float):
        super().__init__()
        self.interval = interval
    
    async def run(self, input, output):
        buffer_input_channel, buffer_output_channel = trio.open_memory_channel(math.inf)

        async def pull_task():
            async with buffer_input_channel, aclosing(input) as aiter:
                async for item in aiter:
                    await buffer_input_channel.send((item, trio.current_time() + self.interval))
        
        async def push_task():
            async with output, buffer_output_channel:
                async for item, timestamp in buffer_output_channel:
                    now = trio.current_time()
                    if timestamp > now:
                        await trio.sleep(timestamp - now)
                    await output.send(item)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(pull_task)
            nursery.start_soon(push_task)