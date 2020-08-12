__version__ = '0.1.0'

from contextlib import asynccontextmanager
from typing import Sequence

import trio

from .abc import Producer, Refiner
from .producers import Extension
from .tap import Tap

class Pipeline:
    def __init__(self, producer: Producer, *refiners: Sequence[Refiner], nursery: trio.Nursery=None):
        self.producer = producer
        self.refiners = refiners
        self._taps = set()
        self._start_pump = trio.Event()
        self._nursery = nursery

    @asynccontextmanager
    async def _start(self):
        async with trio.open_nursery() as nursery:
            self._nursery = nursery
            self._nursery.start_soon(self._pump)
            yield self
            self._nursery.cancel_scope.cancel()

    async def _pump(self):
        await self._start_pump.wait()

        # Start producer
        self._nursery.start_soon(self.producer.run)

        # Start refiners
        for n, refiner in enumerate(self.refiners):
            if n == 0:
                refiner.input = self.producer.output
                self._nursery.start_soon(refiner.run)
            else:
                refiner.input = self.refiners[n-1].output
                self._nursery.start_soon(refiner.run)

        # Output to taps
        async with self.refiners[-1].output as output_channel:
            async for item in output_channel:
                for tap in self._taps:
                    self._nursery.start_soon(tap.send, item)

        # Cleanup
        for tap in self._taps:
            await tap.send_channel.aclose()

    def tap(self, *, max_buffer_size=0, timeout: float=1, retrys: int=3, start_pump=True) -> trio.MemoryReceiveChannel:
        """Create a new output channel for this pipeline.
        """
        send_channel, receive_channel = trio.open_memory_channel(max_buffer_size)
        self._taps.add(Tap(send_channel, timeout, retrys))
        if start_pump:
            self._start_pump.set()
        return receive_channel

    def extension(self, *refiners: Sequence[Refiner]) -> "Pipeline":
        """Extend this pipeline into a new pipeline.
        """
        pipeline = Pipeline(
            Extension(self.tap()),
            refiners,
            nursery=self._nursery
        )
        self._nursery.start_soon(pipeline._pump) # pylint: disable=protected-access
        return pipeline

@asynccontextmanager
async def create_pipeline(producer: Producer, *refiners: Sequence[Refiner]):
    """Create a new pipeline from a producer and a sequence of refiners."""
    pipeline = Pipeline(producer, refiners)
    async with pipeline._start(): # pylint: disable=protected-access
        yield pipeline
