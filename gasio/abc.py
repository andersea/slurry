from abc import ABC, abstractmethod
from typing import AsyncIterable, Any

import trio


class Producer(ABC):
    """Producers are the first section in a pipeline. Producers creates an output, without defining
    any source for that output."""
    def __init__(self):
        super().__init__()

        self._send_output_channel, self._output = trio.open_memory_channel(0)


    @abstractmethod
    async def run(self):
        """The run method must contain the logic that feeds the output of the producer."""

    @property
    def output(self) -> trio.MemoryReceiveChannel:
        """The output is a Trio memory receive channel."""
        return self._output

class Refiner(Producer):
    """Refiners are producers that takes inputs from another producer."""
    def __init__(self):
        super().__init__()

        self._input = None
    
    @property
    def input(self) -> AsyncIterable[Any]:
        """The input source for the refiner."""
        return self._input
    
    @input.setter
    def input(self, value: AsyncIterable[Any]):
        """Set the input source for the refiner."""
        if self._input is None:
            self._input = value
        else:
            raise AttributeError('Input cannot be reassigned.')