__version__ = '0.1.0'

import builtins
import math
from typing import Sequence, Optional

import trio
from async_generator import aclosing, asynccontextmanager

from .abc import Producer, Refiner
from .producers import Extension
from .tap import Tap

class Pipeline:
    def __init__(self, producer: Producer, *refiners: Sequence[Refiner]):
        self.producer = producer
        self.refiners = refiners
        self._taps = set()
        self._start_pump = trio.Event()
        self._nursery: trio.Nursery = None
        
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
        send_channel, receive_channel = trio.open_memory_channel(max_buffer_size)
        self._taps.add(Tap(send_channel, timeout, retrys))
        if start_pump:
            self._start_pump.set()
        return receive_channel
    
    def extension(self, *refiners: Sequence[Refiner]) -> "Pipeline":
        pipeline = Pipeline(
            Extension(self.tap()),
            refiners
        )
        pipeline._nursery = self._nursery
        pipeline._nursery.start_soon(pipeline._pump)
        return pipeline

@asynccontextmanager
async def create_pipeline(producer: Producer, *refiners: Sequence[Refiner]):
    pipeline = Pipeline(producer, refiners)
    async with pipeline._start(): # pylint: disable=not-async-context-manager
        yield pipeline
    
    