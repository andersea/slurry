"""Main Pipeline class"""
__version__ = '0.1.0'

from contextlib import asynccontextmanager
from itertools import chain
from typing import Sequence

import trio
from async_generator import aclosing

from .abc import Section
from .tap import Tap

class Pipeline:
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
        async with trio.open_nursery() as nursery:
            pipeline = cls(*sections, main_nursery=nursery, main_switch=trio.Event())
            nursery.start_soon(pipeline._pump) # pylint: disable=protected-access
            yield pipeline
            nursery.cancel_scope.cancel()

    async def _pump(self):
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
            timeout: float = 1,
            retrys: int = 3,
            start: bool = True) -> trio.MemoryReceiveChannel:
        """Create a new output channel for this pipeline."""
        send_channel, receive_channel = trio.open_memory_channel(max_buffer_size)
        self._taps.add(Tap(send_channel, timeout, retrys))
        if start:
            self._main_switch.set()
        return receive_channel

    def extend(self, *sections: Sequence[Section]) -> "Pipeline":
        """Extend this pipeline into a new pipeline."""
        pipeline = Pipeline(
            self.tap(),
            sections,
            main_nursery=self._main_nursery,
            main_switch=self._main_switch
        )
        self._main_nursery.start_soon(pipeline._pump) # pylint: disable=protected-access
        return pipeline
