""" Abstract Base Classes for building pipeline sections. """
from abc import ABC, abstractmethod
from typing import Any, AsyncIterable, Awaitable, Callable, Iterable, Optional

class Section(ABC):
    """Defines the basic environment api."""

    @abstractmethod
    async def pump(self, input: Optional[AsyncIterable[Any]], output: Callable[[Any], Awaitable[None]]):
        """The pump method contains the machinery that takes input from previous sections, or
        any asynchronous iterable, processes it and pushes it to the output.

        .. note::
            If this section is the first section of a pipeline, the input will be ``None``. In this
            case, the section is expected to produce output independently.

        .. warning::
            The receiving end of the output can be closed by the pipeline or by the downstream
            section at any time. If you try to send an item to an output that has a closed receiver,
            a ``BrokenResourceError`` will be raised. The pipeline knows about this and is prepared
            to handle it for you, but if you need to do some kind of cleanup, like closing network
            connections for instance, you may want to handle this exception yourself.

        :param input: The input data feed. Will be ``None`` for the first ``Section``, as the first
            ``Section`` is expected to supply it's own input.
        :type input: Optional[AsyncIterable[Any]]
        :param output: An awaitable callable used to send output.
        :type output: Callable[[Any], Awaitable[None]]
        """

class AsyncSection(Section):
    """AsyncSection defines an abc for sections that are designed to run in an async event loop."""

    @abstractmethod
    async def refine(self, input: Optional[AsyncIterable[Any]], output: Callable[[Any], Awaitable[None]]):
        """The async section refine method must contain the logic that iterates the input, processes
        the indidual items, and feeds results to the output.

        :param input: The input data feed. Will be ``None`` for the first ``Section``, as the first
            ``Section`` is expected to supply it's own input.
        :type input: Optional[AsyncIterable[Any]]
        :param output: An awaitable callable used to send output.
        :type output: Callable[[Any], Awaitable[None]]
        """

class SyncSection(Section):
    """SyncSection defines an abc for sections that runs synchronous refiners."""

    @abstractmethod
    def refine(self, input: Optional[Iterable[Any]], output: Callable[[Any], None]):
        """The ``SyncSection`` refine method is intended to run normal synchronous python
        code, including code that can block for IO for an any amount of time. Implementations
        of ``SyncSection`` should take care to design a pump method in such a way, that blocking
        happens transparently to the parent async event loop.

        The refine method is designed to have an api that is as close to the async api as
        possible. The input is a synchronous iterable instead of an async iterable, and the
        output is a synchronous callable, similar to a ``Queue.put`` method.

        .. note::
            Slurry includes two implementations of ``SyncSection``.
            :class:`slurry.environments.ThreadSection`, which runs the refine function in
            a background thread, and :class:`slurry.environments.ProcessSection`
            which spawns an independent process that runs the refine method.

        :param input: The input data feed. Like with ordinary sections, this can be ``None`` if
            ``SyncSection`` is the first section in the pipeline.
        :type input: Optional[Iterable[Any]]
        :param output: The callable used to send output.
        :type output: Callable[[Any], None]
        """
