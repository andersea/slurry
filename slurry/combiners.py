"""Pipeline sections for combining multiple inputs into a single output."""
import builtins
import itertools
from typing import Sequence, AsyncIterable

import trio
from async_generator import aclosing

from .abc import Section

class Chain(Section):
    """Chains asynchronous sequences.

    Outputs items from each source in turn, until it is exhausted. If a source never reaches the
    end, remaining sources will not be iterated.

    Chain can be placed as a middle section and will chain the input of the previous section.

    Note:
        By default, the input is added as the first sources. If the input is added last instead
        of first, it will cause backpressure to be applied upstream.

    Args:
        *sources (AsyncIterable[Any]): One or more async iterables that will be chained together.
        place_input (string): Options: 'first' (default)|'last'. """
    def __init__(self, *sources, place_input='first'):
        super().__init__()
        self.sources = sources
        self.place_input = _validate_place_input(place_input)

    async def pump(self, input, output):
        if input is not None:
            if self.place_input == 'first':
                sources = (input, *self.sources)
            elif self.place_input == 'last':
                sources = (*self.sources, input)
        else:
            sources = self.sources
        async with output:
            for source in sources:
                async with aclosing(source) as agen:
                    async for item in agen:
                        await output.send(item)

class Merge(Section):
    """Merges asynchronous sequences.

    Sources are iterated in parallel and items are send from each source, as soon as they become
    available.

    If Merge is used as a middle section, the input will be added to the sources.

    Args:
        *sources (AsyncIterable[Any]): One or more async iterables that will be
            merged together.
    """
    def __init__(self, *sources):
        super().__init__()
        self.sources = sources

    async def pump(self, input, output):
        if input is not None:
            sources = (input, *self.sources)
        else:
            sources = self.sources
        async with output, trio.open_nursery() as nursery:

            async def pull_task(source, output):
                async with output, aclosing(source) as aiter:
                    async for item in aiter:
                        await output.send(item)

            for source in sources:
                nursery.start_soon(pull_task, source, output.clone())

class Zip(Section):
    """Zip asynchronous sequences.

    Sources are iterated in parallel and as soon as all sources have an item available, those
    items are output as a tuple.

    Zip can be used as a middle section, and the pipeline input will be added to the sources.

    Args:
        *sources (AsyncIterable[Any]): One or more async iterables that will be
            merged together.
        place_input (string):  Options: 'first' (default)|'last'.
    """
    def __init__(self, *sources: Sequence[AsyncIterable], place_input='first'):
        super().__init__()
        self.sources = sources
        self.place_input = _validate_place_input(place_input)

    async def pump(self, input, output):
        if input is not None:
            if self.place_input == 'first':
                sources = (input, *self.sources)
            elif self.place_input == 'last':
                sources = (*self.sources, input)
        else:
            sources = self.sources

        async with output:
            with trio.CancelScope() as cancel_scope:
                async def pull_task(source, results, index):
                    try:
                        results[index] = await source.__anext__()
                    except StopAsyncIteration:
                        cancel_scope.cancel()

                while True:
                    results = [None for _ in sources]
                    async with trio.open_nursery() as nursery:
                        for i, source in builtins.enumerate(sources):
                            nursery.start_soon(pull_task, source, results, i)
                    await output.send(tuple(results))

class ZipLatest(Section):
    """Zips asynchronous sequences and yields a result for on every received item.

    Sources are iterated in parallel and a tuple is yielded each time a result is ready
    on any source. The tuple values will be the last received value from each source.

    If any single source is exchausted, all remaining sources will be forcibly closed, and
    the generator will exit.

    Using monitor argument, one or more asynchronous sequences can be added, that will not trigger
    an output by themselves. Their latest value will be stored and added to the output value
    but will only be output if a new item arrives at one of the main sources.

    ZipLatest can be used as a middle section, in which case the upstream pipeline is
    added as an input.

    Args:
        *sources (AsyncIterable[Any]): One or more async iterables that will be
        zipped together.
        partial (bool): If True (default) output will be sent as soon as the first input arrives.
        default (Any): If partial is True, this is used as the default value when no input has
            arrived.
        monitor (Union[AsyncIterable[Any], Sequence[AsyncIterable[Any]]]): Asynchronous sequences to
            monitor.
        place_input (string): Options: 'first' (default)|'last'
        monitor_input (bool): Input is used as a monitored stream instead of a main source.
    """
    def __init__(self, *sources,
                 partial=True,
                 default=None,
                 monitor=(),
                 place_input='first',
                 monitor_input=False):
        super().__init__()
        self.sources = sources
        self.partial = partial
        self.default = default
        self.monitor = monitor
        self.place_input = _validate_place_input(place_input)
        self.monitor_input = monitor_input

    async def pump(self, input, output):
        sources = self.sources
        try:
            iter(self.monitor)
            monitor = self.monitor
        except TypeError:
            monitor = (self.monitor,)

        if input is not None:
            if self.monitor_input:
                if self.place_input == 'first':
                    monitor = (input, *monitor)
                elif self.place_input == 'last':
                    monitor = (*monitor, input)
            else:
                if self.place_input == 'first':
                    sources = (input, *sources)
                elif self.place_input == 'last':
                    sources = (*sources, input)

        results = [self.default for _ in itertools.chain(sources, monitor)]
        ready = [False for _ in results]

        async with output, trio.open_nursery() as nursery:

            async def pull_task(index, source, monitor=False):
                async with aclosing(source) as aiter:
                    async for item in aiter:
                        results[index] = item
                        ready[index] = True
                        if not monitor and (self.partial or False not in ready):
                            await output.send(tuple(results))
                nursery.cancel_scope.cancel()

            for i, source in builtins.enumerate(sources):
                nursery.start_soon(pull_task, i, source)
            for i, source in builtins.enumerate(monitor):
                nursery.start_soon(pull_task, i + len(sources), source, True)

def _validate_place_input(place_input):
    if isinstance(place_input, str):
        if place_input not in ['first', 'last']:
            raise ValueError(f'Invalid place_input argument: {place_input}')
    else:
        raise TypeError('place_input argument has invalid type.')
    return place_input
