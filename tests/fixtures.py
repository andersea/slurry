"""Asynchronous generators for testing sections."""
import math

from typing import Any, Callable, Iterable

from slurry.environments import ThreadSection, ProcessSection
from slurry._utils import safe_aclose

class SyncSquares(ThreadSection):
    def __init__(self, raise_after=math.inf) -> None:
        self.raise_after = raise_after

    def refine(self, input, output):
        for i, j in enumerate(input):
            output(j*j)
            if i == self.raise_after - 1:
                raise RuntimeError('Max iterations reached.')

class SimpleProcessSection(ProcessSection):
    def __init__(self, value) -> None:
        self.value = value

    def refine(self, input, output):
        output(self.value)

class FibonacciSection(ProcessSection):
    def __init__(self, i) -> None:
        self.i = i

    def fibonacci(self, i):
        if i <= 1:
            return i
        else:
            return self.fibonacci(i-1) + self.fibonacci(i-2)

    def refine(self, input: Iterable[Any], output: Callable[[Any], None]):
        for i in range(self.i):
            output(self.fibonacci(i))

class AsyncNonIteratorIterable:
    def __init__(self, source_aiterable):
        self.source_aiterable = source_aiterable

    def __aiter__(self):
        return self.source_aiterable.__aiter__()

class AsyncIteratorWithoutAclose:
    def __init__(self, source_aiterable):
        self.source_aiter = source_aiterable.__aiter__()

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return await self.source_aiter.__anext__()
        except StopAsyncIteration:
            await safe_aclose(self.source_aiter)
            raise
