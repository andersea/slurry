""" Abstract Base Classes for building pipeline sections. """
from abc import ABC, abstractmethod
from typing import Any, AsyncIterable, Awaitable, Callable, Iterable, Optional

class Section(ABC):
    """Each pipeline section takes inputs from an async iterable, processes it and sends it to an
    output.

    A section must implement the :meth:`pump` abstract method, which will be scheduled to run as a task
    by the pipeline. The pump method serves as an underlying machinery for pulling and pushing
    data through the section.

    Each subclass of section must implement a way to process each received item. This should be
    done by either implementing an asynchronous or synchronous refine method. Slurry defines two
    standard apis for implementing a refine method, an asynchronous one as defined by
    :class:`AsyncSection`, and a synchronous as defined by :class:`SyncSection`. The refine api
    is not strictly a requirement, but a convention. Any class that implements the ``Section``
    api is a valid pipeline section.
    """

    @abstractmethod
    async def pump(self, input: Optional[AsyncIterable[Any]], output: Callable[[Any], Awaitable[None]]):
        """The pump method contains the machinery that takes input from previous sections, or
        any asynchronous iterable, processes it and pushes it to the output.

        .. note::
            The receiving end of the output can be closed by the pipeline or by the downstream
            section at any time. If you try to send an item to an output that has a closed receiver,
            a ``BrokenResourceError`` will be raised. The pipeline knows about this and is prepared
            to handle it for you, but if you need to do some kind of cleanup, like closing network
            connections for instance, you may want to handle this exception yourself.

        .. note::
            If this section is the first section of a pipeline, the input will be ``None``. In this
            case, the section is expected to produce output independently.

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

        By default, the pipeline tries to manage the input and output resource lifetime. Normally
        you don't have to worry about closing the input and output after use. The exception is, if
        your custom section adds additional input sources, or provides it's own input. In this case
        the section must take care of closing the input after use.

        :param input: The input data feed. Will be ``None`` for the first ``Section``, as the first
            ``Section`` is expected to supply it's own input.
        :type input: Optional[AsyncIterable[Any]]
        :param output: An awaitable callable used to send output.
        :type output: Callable[[Any], Awaitable[None]]
        """

class SyncSection(Section):
    """Sync defines an abc for sections that runs synchronous refiners. Implementations
    of ``SyncSection`` should be carefully designed so as to not block the underlying
    asynchronous pipeline event loop.

    Async sections and synchronous sections can be freely mixed and matched in the pipeline.
    """

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
