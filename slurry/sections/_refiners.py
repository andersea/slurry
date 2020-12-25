"""Sections for transforming an input into a different output."""
from typing import Any, AsyncIterable, Optional, Union

from async_generator import aclosing

from .abc import Section

class Map(Section):
    """Maps over an asynchronous sequence.

    Map can be used as a starting section, if a source is provided. Both AsyncIterable and Section
    sources are supported.

    :param func: Mapping function.
    :type func: Callable[[Any], Any]
    :param source: Source if used as a starting section.
    :type source: Optional[Union[AsyncIterable[Any], Section]]
    """
    def __init__(self, func, source: Optional[Union[AsyncIterable[Any], Section]] = None):
        super().__init__()
        self.func = func
        self.source = source

    async def pump(self, input, output):
        if input:
            source = input
        elif self.source:
            source = self.source
        else:
            raise RuntimeError('No input provided.')

        if isinstance(source, Section):
            async def _output(item):
                await output(self.func(item))
            await source.pump(None, _output)
        else:
            async with aclosing(source) as aiter:
                async for item in aiter:
                    await output(self.func(item))
