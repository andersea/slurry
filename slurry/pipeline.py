"""Main Pipeline class"""
__version__ = '0.1.0'

from itertools import chain
import math
from typing import Sequence

import trio
from async_generator import aclosing, asynccontextmanager

from .abc import Section
from .tap import Tap

class Pipeline:
    """The ``Pipeline`` is a composable a stream processor. It consists of a chain of
    ``Sections``, which each handle a single stream processing operation.

    The stream processing results are accessed by calling tap to create an output channel.
    Each pipeline can have multiple open tabs, each receiving a copy of the output stream.
    
    The pipeline can also be extended dynamically with new pipeline sections adding
    additional processing.

    Note:
        Do not instantiate a ``Pipeline`` manually. Use ``Pipeline.create`` instead. It
        returns an async context manager which manages the pipeline lifetime.

    Args:
        *sections (Sequence[Section]): One or more pipeline sections.
        main_nursery (trio.Nursery): Nursery used to run data pumping tasks.
        main_switch (trio.Event): Event to control pipeline start.
    """
    def __init__(self, *sections: Sequence[Section],
                 main_nursery: trio.Nursery,
                 main_switch: trio.Event):
        self.sections = sections
        self._taps = set()
        self._main_nursery = main_nursery
        self._main_switch = main_switch

    @classmethod
    @asynccontextmanager
    async def create(cls, *sections: Sequence[Section]):
        """Creates a new pipeline context and adds the given section sequence to it.

        Args:
            *sections (Sequence[Section]): One or more pipeline sections.
        """
        async with trio.open_nursery() as nursery:
            pipeline = cls(*sections, main_nursery=nursery, main_switch=trio.Event())
            nursery.start_soon(pipeline._pump) # pylint: disable=protected-access
            yield pipeline
            nursery.cancel_scope.cancel()

    async def _pump(self):
        """Runs the pipeline."""
        await self._main_switch.wait()

        if isinstance(self.sections[0], Section):
            first_input = None
            sections = self.sections
        else:
            first_input = self.sections[0]
            sections = self.sections[1:]

        channels = chain((first_input,), *(trio.open_memory_channel(0) for _ in sections))

        async with trio.open_nursery() as nursery:

            # Start pumps
            for section in sections:
                nursery.start_soon(section.pump, next(channels), next(channels))

            # Output to taps
            async with aclosing(next(channels)) as aiter:
                async for item in aiter:
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
        """Create a new output channel for this pipeline.

        Multiple channels can be opened and will receive a copy of the output data.

        Note:
            The output is sent by reference, so if a consumer changes it, other consumers
            will see the changed output.

        Args:
            max_buffer_size (int): Although not recommended in general, it is possible to
                set a buffer on the output channel. (default ``0``)
            timeout (float): Timeout in seconds when attempting to send an item.
                (default ``math.inf``)
            retrys (int): Number of times to retry sending, if the initial attempt fails.
                (default ``0``)
            start (bool): Start processesing when opening this tap. (default ``True``)

        Returns:
            trio.MemoryReceiveChannel
        """
        send_channel, receive_channel = trio.open_memory_channel(max_buffer_size)
        self._taps.add(Tap(send_channel, timeout, retrys))
        if start:
            self._main_switch.set()
        return receive_channel

    def extend(self, *sections: Sequence[Section]) -> "Pipeline":
        """Extend this pipeline into a new pipeline.

        Note:
            Extending a pipeline implicitly enables it.

        Args:
            *sections (Sequence[Section]): One or more pipeline sections.
        """
        pipeline = Pipeline(
            self.tap(),
            sections,
            main_nursery=self._main_nursery,
            main_switch=self._main_switch
        )
        self._main_nursery.start_soon(pipeline._pump) # pylint: disable=protected-access
        return pipeline
