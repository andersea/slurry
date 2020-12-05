""" Abstract Base Classes for building pipeline sections. """
from abc import ABC, abstractmethod
from typing import Any, AsyncIterable, Optional

import trio

class Section(ABC):
    """Each pipeline section takes inputs from an async iterable, processes it and sends it to an
    output.

    A Section must implement the ``pump`` abstract method, which will be scheduled to run as a task
    by the pipeline.
    """

    @abstractmethod
    async def pump(self, input: Optional[AsyncIterable[Any]], output: trio.MemorySendChannel):
        """The pump method must contain the logic that iterates the input, processes the indidual
        items, and feeds results to the output.

        By default, the pipeline tries to manage the input and output resource lifetime. Normally
        you don't have to worry about closing the input and output after use. The exception is, if
        your custom section adds additional input sources, or provides it's own input. In this case
        the section must take care of closing the input after use.

        .. note::
            The receiving end of the output can be closed by the pipeline or by the downstream
            section at any time. If you try to send an item to an output that has a closed receiver,
            a ``BrokenResourceError`` will be raised. The pipeline knows about this and is prepared
            to handle it for you, but if you need to do some kind of cleanup, like closing network
            connections for instance, you may want to handle this exception yourself.

        :param input: The input data feed. Will be ``None`` for the first ``Section``, as the first
            ``Section`` is expected to supply it's own input.
        :type input: Optional[AsyncIterable[Any]]
        :param output: The output memory channel where results are sent.
        :type output: trio.MemorySendChannel
        """
