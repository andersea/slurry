"""Contains the main Slurry ``Pipeline`` class."""

import math
from typing import AsyncContextManager, Sequence

import trio
from async_generator import aclosing, asynccontextmanager

from .sections.weld import weld
from ._tap import Tap

class Pipeline:
    """The main Slurry ``Pipeline`` class.

    .. note::
        Do not instantiate a ``Pipeline`` class manually. Use :meth:`create`
        instead. It returns an async context manager which manages the pipeline lifetime.

    Fields:

    * ``sections``: The sequence of pipeline sections contained in the pipeline.
    * ``nursery``: The :class:`trio.Nursery` that is executing the pipeline.

    """
    def __init__(self, *sections: Sequence["PipelineSection"],
                 nursery: trio.Nursery,
                 enabled: trio.Event):
        self.sections = sections
        self.nursery = nursery
        self._enabled = enabled
        self._taps = set()

    @classmethod
    @asynccontextmanager
    async def create(cls, *sections: Sequence["PipelineSection"]) -> AsyncContextManager["Pipeline"]:
        """Creates a new pipeline context and adds the given section sequence to it.

        :param Sequence[PipelineSection] \\*sections: One or more
          :mod:`PipelineSection <slurry.sections.weld>` compatible objects.
        """
        async with trio.open_nursery() as nursery:
            pipeline = cls(*sections, nursery=nursery, enabled=trio.Event())
            nursery.start_soon(pipeline._pump) # pylint: disable=protected-access
            yield pipeline
            nursery.cancel_scope.cancel()

    async def _pump(self):
        """Runs the pipeline."""
        await self._enabled.wait()

        async with trio.open_nursery() as nursery:
            output = weld(nursery, *self.sections)

            # Output to taps
            async with aclosing(output) as aiter:
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

    def extend(self, *sections: Sequence["PipelineSection"], start: bool = False) -> "Pipeline":
        """Extend this pipeline into a new pipeline.
        
        An extension will add a tap to the existing pipeline and use this tap as input to the
        newly added pipeline.
        
        Extensions can be added dynamically during runtime. The data feed
        will start at the current position. Old events won't be replayed.

        :param Sequence[PipelineSection] \\*sections: One or more pipeline sections.
        :param bool start: Start processing when adding this extension. (default: ``False``)
        """
        pipeline = Pipeline(
            self.tap(start=start),
            sections,
            nursery=self.nursery,
            enabled=self._enabled
        )
        self.nursery.start_soon(pipeline._pump) # pylint: disable=protected-access
        return pipeline
