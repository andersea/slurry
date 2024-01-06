"""The Trio environment implements ``TrioSection``, which is a Trio-native 
:class:`AsyncSection <slurry.sections.abc.AsyncSection>`."""
from typing import Any, Awaitable, Callable, Optional

from ..sections.abc import AsyncSection
from .._types import AsyncIterableWithAcloseableIterator

class TrioSection(AsyncSection):
    """Since Trio is the native Slurry event loop, this environment is simple to implement.
    The pump method does not need to do anything special to bridge the input and output. It
    simply delegates directly to the refine method, as the api is identical."""
    async def pump(
        self, input: Optional[AsyncIterableWithAcloseableIterator[Any]], output: Callable[[Any], Awaitable[None]]
    ):
        """Calls refine."""
        await self.refine(input, output)
