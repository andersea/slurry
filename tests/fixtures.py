"""Asynchronous generators for testing sections."""
import math

import string
from typing import Any, Callable, Iterable

import trio

from slurry.sections.threading import ThreadSection
from slurry.sections.multiprocessing import ProcessSection

async def produce_increasing_integers(interval, *, max=3, delay=0):
    await trio.sleep(delay)
    for i in range(max):
        yield i
        if i == max-1:
            break
        await trio.sleep(interval)

async def produce_alphabet(interval, *, max=3, delay=0):
    await trio.sleep(delay)
    for i, c in enumerate(string.ascii_lowercase):
        yield c
        if i == max - 1:
            break
        await trio.sleep(interval)

async def spam_wait_spam_integers(interval):
    async for i in produce_increasing_integers(.1, max=5, delay=.1):
        yield i
    await trio.sleep(interval)
    async for i in produce_increasing_integers(.1, max=5, delay=.1):
        yield i

async def produce_mappings(interval):
    vehicles = [
        {'vehicle': 'motorcycle'},
        {'vehicle': 'car'},
        {'vehicle': 'motorcycle'},
        {'vehicle': 'autocamper'},
        {'vehicle': 'car'},
        {'vehicle': 'car'},
        {'vehicle': 'truck'},
        {'vehicle': 'car'},
        {'vehicle': 'motorcycle'},
    ]

    for i, vehicle in enumerate(vehicles):
        vehicle['number'] = i
        yield vehicle
        await trio.sleep(interval)

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
