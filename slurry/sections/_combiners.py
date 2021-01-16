"""Pipeline sections for combining multiple inputs into a single output."""
import builtins
import itertools
from typing import Any, AsyncIterable, Sequence

import trio
from async_generator import aclosing

from ..environments import TrioSection
from .weld import weld

class Chain(TrioSection):
    """Chains input from one or more sources. Any valid ``PipelineSection`` is an allowed source.

    Outputs items from each source in turn, until it is exhausted. If a source never reaches the
    end, remaining sources will not be iterated.

    Chain can be placed as a middle section and will chain the input of the previous section.

    .. Note::
        By default, the input is added as the first source. If the input is added last instead
        of first, it will cause backpressure to be applied upstream.

    :param sources: One or more ``PipelineSection`` that will be chained together.
    :type sources: Sequence[PipelineSection]
    :param place_input: Iteration priority of the pipeline input source. Options:
        ``'first'`` (default) \\| ``'last'``.
    :type place_input: string
    """
    def __init__(self, *sources: Sequence["PipelineSection"], place_input='first'):
        super().__init__()
        self.sources = sources
        self.place_input = _validate_place_input(place_input)

    async def refine(self, input, output):
        if input:
            if self.place_input == 'last':
                sources = (*self.sources, input)
            else:
                sources = (input, *self.sources)
        else:
            sources = self.sources
        async with trio.open_nursery() as nursery:
            for source in sources:
                async with aclosing(weld(nursery, source)) as agen:
                    async for item in agen:
                        await output(item)

class Merge(TrioSection):
    """Merges input from multiple sources. Any valid ``PipelineSection`` is an allowed source.

    Sources are iterated in parallel and items are send from each source, as soon as
    they become available.

    If Merge is used as a middle section, the input will be added to the sources.

    Sources can be pipeline sections, which will be treated as first sections, with
    no input. Merge will take care of running the pump task for these sections.

    :param sources: One or more async iterables or sections who's contents will be merged.
    :type sources: Sequence[PipelineSection]
    """
    def __init__(self, *sources: Sequence["PipelineSection"]):
        super().__init__()
        self.sources = sources

    async def refine(self, input, output):
        async with trio.open_nursery() as nursery:

            async def pull_task(source):
                async with aclosing(weld(nursery, source)) as aiter:
                    async for item in aiter:
                        await output(item)

            if input:
                nursery.start_soon(pull_task, input)

            for source in self.sources:
                nursery.start_soon(pull_task, source)

class Zip(TrioSection):
    """Zips the input from multiple sources. Any valid ``PipelineSection`` is an allowed source.

    Sources are iterated in parallel and as soon as all sources have an item available, those
    items are output as a tuple.

    Zip can be used as a middle section, and the pipeline input will be added to the sources.

    .. Note::
        If sources are out of sync, the fastest source will have to wait for the slowest, which
        will cause backpressure.

    :param sources:  One or more ``PipelineSection``, who's contents will be zipped.
    :type sources: Sequence[PipelineSection]
    :param place_input:  Position of the pipeline input source in the output tuple. Options:
        ``'first'`` (default) \\| ``'last'``.
    :type place_input: string
    """
    def __init__(self, *sources: Sequence["PipelineSection"], place_input='first'):
        super().__init__()
        self.sources = sources
        self.place_input = _validate_place_input(place_input)

    async def refine(self, input, output):
        if input:
            if self.place_input == 'last':
                sources = (*self.sources, input)
            else:
                sources = (input, *self.sources)
        else:
            sources = self.sources

        async with trio.open_nursery() as weld_nursery:
            sources = [weld(weld_nursery, source) for source in sources]

            async def pull_task(source, index, results: list):
                try:
                    results.append((index, await source.__anext__()))
                except StopAsyncIteration:
                    weld_nursery.cancel_scope.cancel()

            while True:
                results = []
                async with trio.open_nursery() as pull_nursery:
                    for i, source in builtins.enumerate(sources):
                        pull_nursery.start_soon(pull_task, source, i, results)
                await output(tuple(result for i, result in sorted(results, key=lambda packet: packet[0])))

        for source in sources:
            await source.aclose()

class ZipLatest(TrioSection):
    """Zips input from multiple sources and outputs a result on every received item. Any valid
    ``PipelineSection`` is an allowed source.

    Sources are iterated in parallel and a tuple is output each time a result is ready
    on any source. The tuple values will be the last received value from each source.

    Using the monitor argument, one or more asynchronous sequences can be added with the property
    that they will not trigger an output by themselves. Their latest value will be stored and
    added to the output value, but will only be output if a new item arrives at one of the main
    sources.

    ZipLatest can be used as a middle section, in which case the upstream pipeline is
    added as an input.

    .. Note::
        If any single source is exchausted, all remaining sources will be forcibly closed, and
        the pipeline will stop.

    :param sources: One or more async iterables that will be zipped together.
    :type sources: Sequence[AsyncIterable[Any]]
    :param partial: If ``True`` (default) output will be sent as soon as the first input arrives.
        Otherwise, all main sources must send at least one item, before an output is generated.
    :type partial: bool
    :param default: If the parameter ``partial`` is ``True``, this value is used as the
        default value to output, until an input has arrived on a source. Defaults to ``None``.
    :type default: Any
    :param monitor: Additional asynchronous sequences to monitor.
    :type monitor: Optional[Union[AsyncIterable[Any], Sequence[AsyncIterable[Any]]]]
    :param place_input: Position of the pipeline input source in the output tuple. Options:
        ``'first'`` (default)|``'last'``
    :type place_input: string
    :param monitor_input: Input is used as a monitored stream instead of a main source.
        Defaults to ``False``
    :type monitor_input: bool
    """
    def __init__(self, *sources: Sequence["PipelineSection"],
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

    async def refine(self, input, output):
        sources = self.sources
        try:
            iter(self.monitor)
            monitor = self.monitor
        except TypeError:
            monitor = (self.monitor,)

        if input is not None:
            if self.monitor_input:
                if self.place_input == 'last':
                    monitor = (*monitor, input)
                else:
                    monitor = (input, *monitor)
            else:
                if self.place_input == 'last':
                    sources = (*sources, input)
                else:
                    sources = (input, *sources)

        results = [self.default for _ in itertools.chain(sources, monitor)]
        ready = [False for _ in results]

        async with trio.open_nursery() as nursery:

            async def pull_task(index, source, monitor=False):
                async with aclosing(weld(nursery, source)) as aiter:
                    async for item in aiter:
                        results[index] = item
                        ready[index] = True
                        if not monitor and (self.partial or False not in ready):
                            await output(tuple(results))
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
