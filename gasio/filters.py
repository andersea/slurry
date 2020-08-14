from .abc import Refiner

class Skip(Refiner):
    """Skips the first n items in an asynchronous sequence."""
    def __init__(self, n: int):
        super().__init__()
        self.n = n

    async def run(self, input, output):
        async with aclosing(input) as aiter, output:
            for _ in range(self.n):
                await aiter.__anext__()
            async for item in aiter:
                await output.send(item)

class Filter(Refiner):
    """Outputs items that match a filter.

    The filter function must take an item. If the return value evaluates as true, the item is sent,
    otherwise the item is discarded."""
    def __init__(self, func):
        super().__init__()
        self.func = func

    async def run(self, input, output):
        async with aclosing(input) as aiter, output:
            async for item in aiter:
                if func(item):
                    await output.send(item)

class Changes(Refiner):
    """Outputs items that are different from the last item output.

    The generator stores a reference to the last output item. Whenever a new item arrives, it is
    compared to the previously output item. If they are equal, the new item is discarded. If not,
    the new item is output and becomes the new reference. The first item received is always outputted.
    
    Note: Items are compared using the != operator.
    """

    async def run(self, input, output):
        token = object()
        last = token
        async with aclosing(input) as aiter, output:
            async for item in aiter:
                if last is token or item != last:
                    last = item
                    await output.send(item)
