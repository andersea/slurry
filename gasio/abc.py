from abc import ABC, abstractmethod
from typing import AsyncIterable, Any

import trio

class Refiner(ABC):
    """Refiners takes inputs from an async iterable, processes it and sends it to an output."""

    @abstractmethod
    async def run(self, input: AsyncIterable[Any], output: trio.MemorySendChannel):
        """The run method must contain the logic that iterates the input, processes the
        indidual items, and feeds results to the output."""

class Mixer(ABC):
    """Mixers are special pipeline sections that can be used to start a pipeline. Mixers
    creates an output from multiple inputs."""

    @abstractmethod
    async def run(self, output: trio.MemorySendChannel):
        """The run method must contain the logic that feeds the output of the producer."""

