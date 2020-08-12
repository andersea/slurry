from abc import ABC, abstractmethod

class Producer(ABC):
    """Producers are the first section in a pipeline. Producers creates an output, without defining
    any source for that output."""

    @abstractmethod
    async def run(self):
        """The run method must contain the logic that feeds the output of the producer."""

    @property
    @abstractmethod
    def output(self):
        """The output is a Trio memory receive channel."""

class Refiner(Producer):
    """Refiners are producers that takes inputs from another producer."""
    
    @property
    @abstractmethod
    def input(self):
        """The input source for the producer."""
