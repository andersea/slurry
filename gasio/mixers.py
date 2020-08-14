import builtins
from typing import Sequence, AsyncIterable

import trio
from async_generator import aclosing

from .abc import Mixer

class Chain(Mixer):
    """Chains asynchronous sequences.

    Outputs items from each source in turn, until it is exhausted. If a source never reaches the
    end, remaining sources will not be iterated."""
    def __init__(self, *sources):
        super().__init__()
        self.sources = sources

    async def run(self, output):
        for source in self.sources:
            async with aclosing(source) as agen:
                async for item in agen:
                    await output.send(item)

class Merge(Mixer):
    """Merges asynchronous sequences.

    Sources are iterated in parallel and items are send from each source, as soon as they become
    available."""
    def __init__(self, *sources):
        super().__init__()
        self.sources = sources

    async def run(self, output):
        async with trio.open_nursery() as nursery:

            async def pull_task(source):
                async with output.clone() as send_channel, aclosing(source) as aiter:
                    async for item in aiter:
                        await send_channel.send(item)

            for source in self.sources:
                nursery.start_soon(pull_task, source)

class Zip(Mixer):
    def __init__(self, *sources: Sequence[AsyncIterable]):
        super().__init__()

        self.sources = sources

    async def run(self, output):
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
            async with output:
                while True:
                    await output.send(tuple([await r.receive() for _, r in results]))
                    for p, _ in pull_controls:
                        await p.send(None)

class ZipLatest(Mixer):
    def __init__(self, *sources, partial=True, default=None, monitor=()):
        super().__init__()
        self.sources = sources
        self.partial = partial
        self.default = default
        self.monitor = monitor

    async def run(self, output):
        """Zips asynchronous sequences and yields a result for on every received item.

        Sources are iterated in parallel and a tuple is yielded each time a result is ready
        on any source. The tuple values will be the last received value from each source.
        
        If any single source is exchausted, all remaining sources will be forcibly closed, and
        the generator will exit.
        """
        async with trio.open_nursery() as nursery:
            try:
                iter(self.monitor)
                monitor = self.monitor
            except TypeError:
                monitor = (self.monitor,)
            results = [self.default for _ in itertools.chain(self.sources, monitor)]
            ready = [False for _ in results]
            send_notify, receive_notify = trio.open_memory_channel(0)

            async def pull_task(index, source, monitor=False):
                async with aclosing(source) as agen:
                    async for item in agen:
                        results[index] = item
                        ready[index] = True
                        if not monitor:
                            await send_notify.send(None)
                nursery.cancel_scope.cancel()

            for i, s in builtins.enumerate(self.sources):
                nursery.start_soon(pull_task, i, s)
            for i, s in builtins.enumerate(monitor):
                nursery.start_soon(pull_task, i + len(self.sources), s, True)

            if not self.partial:
                while False in ready:
                    await receive_notify.receive()
                await output.send(tuple(results))
            async for _ in receive_notify:
                await output.send(tuple(results))
