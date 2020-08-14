import math

import trio
from async_generator import aclosing

from .abc import Refiner

class Map(Refiner):
    def __init__(self, func):
        super().__init__()
        self.func = func
    
    async def run(self, input, output):
        async with input, output:
            async for item in input:
                await output.send(self.func(item))

