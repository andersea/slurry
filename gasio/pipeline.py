__version__ = '0.1.0'

from contextlib import asynccontextmanager
from typing import Sequence, AsyncIterable, Any, Union

import trio

from .abc import Producer, Refiner
from .tap import Tap

class Pipeline:
    def __init__(self, producer: Union[Producer, AsyncIterable[Any]], *refiners: Sequence[Refiner], nursery: trio.Nursery=None):
        self.producer = producer
        self.refiners = refiners
        self._taps = set()
        self._start_pump = trio.Event()
        self._nursery = nursery

    @classmethod
    @asynccontextmanager
    async def create(cls, producer: Union[Producer, AsyncIterable[Any]], *refiners: Sequence[Refiner]):
        pipeline = cls(producer, *refiners)
        async with trio.open_nursery() as nursery:
            pipeline._nursery = nursery
            pipeline._nursery.start_soon(pipeline._pump)
            yield pipeline
            pipeline._nursery.cancel_scope.cancel()

    async def _pump(self):
        await self._start_pump.wait()

        # Start producer
        if isinstance(self.producer, Producer):
            self._nursery.start_soon(self.producer.run)

        # Start refiners
        for n, refiner in enumerate(self.refiners):
            if n == 0:
                if isinstance(self.producer, Producer):
                    refiner.input = self.producer.output
                else:
                    # Assumes producer is AsyncIterable
                    refiner.input = self.producer
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

    def extend(self, *refiners: Sequence[Refiner]) -> "Pipeline":
        """Extend this pipeline into a new pipeline.
        """
        pipeline = Pipeline(
            self.tap(),
            refiners,
            nursery=self._nursery
        )
        self._nursery.start_soon(pipeline._pump) # pylint: disable=protected-access
        return pipeline
