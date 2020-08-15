"""Sections for transforming an input into a different output."""
from async_generator import aclosing

from .abc import Section

class Map(Section):
    """Maps over an asynchronous sequence.

    Map can be used as a starting section, if a source is provided.

    Args:
        func (Callable[[Any], Any]): Mapping function.
        source (AsyncIterable[Any]): Source if used as a starting section.
    """
    def __init__(self, func, source=None):
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
                await output.send(self.func(item))
