"""Pipeline sections that filters the incoming items."""
from typing import Any, AsyncIterable, Callable, Hashable, Optional, Union

from async_generator import aclosing
import trio

from ..environments import TrioSection

class Skip(TrioSection):
    """Skips the first ``count`` items in an asynchronous sequence.

    Skip can be used as a starting section if a source is given.

    :param count: Number of items to skip
    :type count: int
    :param source: Input source if starting section.
    :type source: Optional[AsyncIterable[Any]]
    """
    def __init__(self, count: int, source: Optional[AsyncIterable[Any]] = None):
        super().__init__()
        self.count = count
        self.source = source

    async def refine(self, input, output):
        if input:
            source = input
        elif self.source:
            source = self.source
        else:
            raise RuntimeError('No input provided.')

        async with aclosing(source) as aiter:
            try:
                for _ in range(self.count):
                    await aiter.__anext__()
            except StopAsyncIteration:
                return
            async for item in aiter:
                await output(item)

class Filter(TrioSection):
    """Outputs items that passes a filter function.

    The filter function must take an item. If the return value evaluates as true, the item is sent,
    otherwise the item is discarded.

    Filter can be used as a starting section, if a source is provided.

    :param func: Matching function.
    :type func: Callable[[Any], bool]
    :param source: Source if used as a starting section.
    :type source: Optional[AsyncIterable[Any]]
    """
    def __init__(self, func, source: Optional[AsyncIterable[Any]] = None):
        super().__init__()
        self.func = func
        self.source = source

    async def refine(self, input, output):
        if input:
            source = input
        elif self.source:
            source = self.source
        else:
            raise RuntimeError('No input provided.')

        async with aclosing(source) as aiter:
            async for item in aiter:
                if self.func(item):
                    await output(item)

class Changes(TrioSection):
    """Outputs items that are different from the last item output.

    The generator stores a reference to the last outputted item. Whenever a new item arrives, it is
    compared to the last outputted item. If they are equal, the new item is discarded. If not,
    the new item is output and becomes the new reference. The first item received is always
    output.

    Changes can be used as a starting section, if a source is provided.

    .. Note::
        Items are compared using the != operator.

    :param source: Source if used as a starting section.
    :type source: Optional[AsyncIterable[Any]]
    """
    def __init__(self, source: Optional[AsyncIterable[Any]] = None):
        super().__init__()
        self.source = source

    async def refine(self, input, output):
        if input:
            source = input
        elif self.source:
            source = self.source
        else:
            raise RuntimeError('No input provided.')

        token = object()
        last = token
        async with aclosing(source) as aiter:
            async for item in aiter:
                if last is token or item != last:
                    last = item
                    await output(item)

class RateLimit(TrioSection):
    """Limits data rate of an input to a certain interval.

    The first item received is transmitted and triggers a timer. Any other items received while
    the timer is active are discarded. After the timer runs out, the cycle can repeat.

    Per subject rate limiting is supported by supplying either a hashable value or a callable as
    subject.
    In case of a hashable value, each received item is assumed to be a mapping, with the subject
    indicating the key containing the value that should be used for rate limiting.
    If a callable is supplied, it will be called with the item as argument and should return a
    hashable value.

    :param interval: Minimum number of seconds between each sent item.
    :type interval: float
    :param source: Input when used as first section.
    :type source: Optional[AsyncIterable[Any]]
    :param subject: Subject for per subject rate limiting.
    :type subject: Optional[]
    """
    def __init__(self,
                 interval,
                 source: Optional[AsyncIterable[Any]] = None,
                 *,
                 subject: Optional[Union[Hashable, Callable[[Any], Hashable]]] = None):
        super().__init__()
        self.source = source
        self.interval = interval
        self.subject = subject

    async def refine(self, input, output):
        if input:
            source = input
        elif self.source:
            source = self.source
        else:
            raise RuntimeError('No input provided.')

        if self.subject is None:
            get_subject = lambda item: None
        elif callable(self.subject):
            get_subject = self.subject
        else:
            get_subject = lambda item: item[self.subject]

        timestamps = {}
        async with aclosing(source) as aiter:
            async for item in aiter:
                now = trio.current_time()
                subject = get_subject(item)
                then = timestamps.get(subject)
                if then is None or now - then > self.interval:
                    timestamps[subject] = now
                    await output(item)
