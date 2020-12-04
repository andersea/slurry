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

        .. note::
            When implementing sections, it is important to gracefully handle channel closures. When
            the upstream iterable is exhausted, close the downstream channel, and vice versa if the
            downstream channel is closed, propagate the closure upstream. The easiest way to do this
            is usually to use a context manager.

            Example:

            .. code-block:: python

                async with aclosing(input) as aiter, output:
                    # .. process input and send to output


        :param input: The input data feed. Will be ``None`` for the first ``Section``, as the first
            ``Section`` is expected to supply it's own input.
        :type input: Optional[AsyncIterable[Any]]
        :param output: The output memory channel where results are sent.
        :type output: trio.MemorySendChannel
        """
