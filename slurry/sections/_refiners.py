"""Sections for transforming an input into a different output."""
from typing import Any, AsyncIterable, Optional

from async_generator import aclosing

from ..environments import TrioSection

class Map(TrioSection):
    """Maps over an asynchronous sequence.

    Map can be used as a starting section, if a source is provided.

    :param func: Mapping function.
    :type func: Callable[[Any], Any]
    :param source: Source if used as a starting section.
    :type source: Optional[AsyncIterable[Any]]
    """
    def __init__(self, func, source: Optional[AsyncIterable[Any]] = None):
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
                await output(self.func(item))
