"""The :class:`Pipeline` class is a composable a stream processor. It consists of a chain of
:class:`slurry.abc.Section`, which each handle a single stream processing operation.

The stream processing results are accessed by calling :meth:`Pipeline.tap` to create an
output channel. Each pipeline can have multiple open taps, each receiving a copy of the
output stream.

The pipeline can also be extended dynamically with new pipeline sections with
:meth:`Pipeline.extend`, adding additional processing.
"""

from itertools import chain
import math
from typing import AsyncContextManager, Sequence

import trio
from async_generator import aclosing, asynccontextmanager

from .sections.abc import Section, ThreadSection, ProcessSection
from .sections.pump import pump
from .tap import Tap


class Pipeline:
    """The main Slurry ``Pipeline`` class.

    .. note::
        Do not instantiate a ``Pipeline`` class manually. Use :meth:`create`
        instead. It returns an async context manager which manages the pipeline lifetime.

    Fields:

    * ``sections``: The ``Sequence`` of pipeline sections contained in the pipeline.
    * ``nursery``: The :class:`trio.Nursery` that is executing the pipeline.

    """
    def __init__(self, *sections: Sequence[Section],
                 nursery: trio.Nursery,
                 enabled: trio.Event):
        self.sections = sections
        self.nursery = nursery
        self._enabled = enabled
        self._taps = set()

    @classmethod
    @asynccontextmanager
    async def create(cls, *sections: Sequence[Section]) -> AsyncContextManager["Pipeline"]:
        """Creates a new pipeline context and adds the given section sequence to it.

        :param sections: One or more pipeline sections.
            It is valid to supply an async iterable instead of a :class:`Section` as *first*
            section.
        :type sections: Sequence[slurry.abc.Section]
        """
        async with trio.open_nursery() as nursery:
            pipeline = cls(*sections, nursery=nursery, enabled=trio.Event())
            nursery.start_soon(pipeline._pump) # pylint: disable=protected-access
            yield pipeline
            nursery.cancel_scope.cancel()

    async def _pump(self):
        """Runs the pipeline."""
        await self._enabled.wait()

        if isinstance(self.sections[0], (Section, ThreadSection, ProcessSection)):
            first_input = None
            sections = self.sections
        else:
            first_input = self.sections[0]
            sections = self.sections[1:]

        channels = chain((first_input,), *(trio.open_memory_channel(0) for _ in sections))

        async with trio.open_nursery() as nursery:

            # Start pumps
            for section in sections:
                nursery.start_soon(pump, section, next(channels), next(channels))

            # Output to taps
            async with aclosing(next(channels)) as aiter:
                async for item in aiter:
                    self._taps = set(filter(lambda tap: not tap.closed, self._taps))
                    if not self._taps:
                        # Hmm.. Debatable. Should closing all taps close the pipeline?
                        break
                    for tap in self._taps:
                        nursery.start_soon(tap.send, item)

        # There is no more output to send. Close the taps.
        for tap in self._taps:
            await tap.send_channel.aclose()

    def tap(self, *,
            max_buffer_size: int = 0,
            timeout: float = math.inf,
            retrys: int = 0,
            start: bool = True) -> trio.MemoryReceiveChannel:
        # pylint: disable=line-too-long
        """Create a new output channel for this pipeline.

        Multiple channels can be opened and will receive a copy of the output data.

        If all open taps are closed, the immidiate upstream section or iterable will be closed as well, and no
        further items can be sent, from that point on.

        .. note::
            The output is sent by reference, so if the output is a mutable type and
            a consumer changes it, other consumers will see the changed output.

        :param max_buffer_size: Although not recommended in general, it is possible to
            set a buffer on the output channel. (default ``0``) See
            `Buffering in channels <https://trio.readthedocs.io/en/stable/reference-core.html#buffering-in-channels>`_
            for further advice.
        :type max_buffer_size: int
        :param timeout: Timeout in seconds when attempting to send an item. (default ``math.inf``)
        :type timeout: float
        :param retrys: Number of times to retry sending, if the initial attempt fails.
            (default ``0``)
        :type retrys: int
        :param start: Start processesing when opening this tap. (default ``True``)
        :type start: bool

        :return: A trio ``MemoryReceiveChannel`` from which pipeline output can be pulled.
        """
        send_channel, receive_channel = trio.open_memory_channel(max_buffer_size)
        self._taps.add(Tap(send_channel, timeout, retrys))
        if start:
            self._enabled.set()
        return receive_channel

    def extend(self, *sections: Sequence[Section], start: bool = False) -> "Pipeline":
        """Extend this pipeline into a new pipeline.

        :param sections: One or more pipeline sections.
        :type sections: Sequence[Section]
        :param start: Start processing when adding this extension. (default: ``False``)
        :type start: bool
        """
        pipeline = Pipeline(
            self.tap(start=start),
            sections,
            nursery=self.nursery,
            enabled=self._enabled
        )
        self.nursery.start_soon(pipeline._pump) # pylint: disable=protected-access
        return pipeline
