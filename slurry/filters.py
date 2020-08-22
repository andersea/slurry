"""Pipeline sections that filter the incoming items."""
from typing import Any, AsyncIterable, Optional

from async_generator import aclosing

from .abc import Section

class Skip(Section):
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

    async def pump(self, input, output):
        if input is None:
            if self.source is not None:
                input = self.source
            else:
                raise RuntimeError('No input provided.')
        async with aclosing(input) as aiter, output:
            for _ in range(self.count):
                await aiter.__anext__()
            async for item in aiter:
                await output.send(item)

class Filter(Section):
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

    async def pump(self, input, output):
        if input is None:
            if self.source is not None:
                input = self.source
            else:
                raise RuntimeError('No input provided.')

        async with aclosing(input) as aiter, output:
            async for item in aiter:
                if self.func(item):
                    await output.send(item)

class Changes(Section):
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

    async def pump(self, input, output):
        if input is None:
            if self.source is not None:
                input = self.source
            else:
                raise RuntimeError('No input provided.')
        token = object()
        last = token
        async with aclosing(input) as aiter, output:
            async for item in aiter:
                if last is token or item != last:
                    last = item
                    await output.send(item)
