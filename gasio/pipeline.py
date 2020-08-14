__version__ = '0.1.0'

from contextlib import asynccontextmanager
from itertools import chain
from typing import Sequence, AsyncIterable, Any, Union

import trio
from async_generator import aclosing

from .abc import Mixer, Refiner
from .tap import Tap

class Pipeline:
    def __init__(self, producer: Union[Mixer, AsyncIterable[Any]], *refiners: Sequence[Refiner], main_nursery: trio.Nursery, main_switch: trio.Event):
        self.producer = producer
        self.refiners = refiners
        self._taps = set()
        self._main_nursery = main_nursery
        self._main_switch = main_switch

    @classmethod
    @asynccontextmanager
    async def create(cls, producer: Union[Mixer, AsyncIterable[Any]], *refiners: Sequence[Refiner]):
        async with trio.open_nursery() as nursery:
            pipeline = cls(producer, *refiners, main_nursery=nursery, main_switch=trio.Event())
            nursery.start_soon(pipeline._pump)
            yield pipeline
            nursery.cancel_scope.cancel()

    async def _pump(self):
        await self._main_switch.wait()

        refiner_channels = (trio.open_memory_channel(0) for _ in self.refiners)

        async with trio.open_nursery() as nursery:

            # Start producer
            if isinstance(self.producer, Mixer):
                channels = chain(trio.open_memory_channel(0), *refiner_channels)
                nursery.start_soon(self.producer.run, next(channels))
            else:
                channels = chain((self.producer, ), *refiner_channels)

            # Start refiners
            for refiner in self.refiners:
                nursery.start_soon(refiner.run, next(channels), next(channels))

            # Output to taps
            async with aclosing(next(channels)) as aiter:
                async for item in aiter:
                    for tap in self._taps:
                        nursery.start_soon(tap.send, item)

        # There is no more output to send. Close the taps.
        for tap in self._taps:
            await tap.send_channel.aclose()

    def tap(self, *, max_buffer_size=0, timeout: float=1, retrys: int=3, start=True) -> trio.MemoryReceiveChannel:
        """Create a new output channel for this pipeline."""
        send_channel, receive_channel = trio.open_memory_channel(max_buffer_size)
        self._taps.add(Tap(send_channel, timeout, retrys))
        if start:
            self._main_switch.set()
        return receive_channel

    def extend(self, *refiners: Sequence[Refiner]) -> "Pipeline":
        """Extend this pipeline into a new pipeline."""
        pipeline = Pipeline(
            self.tap(),
            refiners,
            main_nursery=self._main_nursery,
            main_switch=self._main_switch
        )
        self._main_nursery.start_soon(pipeline._pump) # pylint: disable=protected-access
        return pipeline
