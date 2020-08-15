""" Abstract Base Classes for building pipeline sections. """
from abc import ABC, abstractmethod
from typing import Any, AsyncIterable, Union

import trio

class Section(ABC):
    """Each pipeline section takes inputs from an async iterable, processes it and sends it to an
    output.
    """

    @abstractmethod
    async def pump(self, input: Union[AsyncIterable[Any], None], output: trio.MemorySendChannel):
        """The run method must contain the logic that iterates the input, processes the indidual
        items, and feeds results to the output.

        The first section of the pipeline does not receive an input. It is expected to supply
        itself.
        """
