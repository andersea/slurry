"""Pipeline sections with age- and volume-based buffers."""
from collections import deque
import math
from typing import Any, Callable, Sequence

import trio
from async_generator import aclosing

from .abc import Section

class FiloBuffer(Section):
    """First in-last out sequence buffer with optional.

    Iterates an asynchronous sequence and puts each received item in a buffer..
    When an item is received, the buffer is filtered by dumping the oldest items first, until the
    size of the buffer is equal to max_size or less. The buffer is then output as a tuple.

    If an interval is given, items have a time limit, after which the item is discarded, when
    filtering occurs.

    It is possible to set a minimum buffer size. If the buffer is shorter than min_size, items will
    be added, but the buffer will not be yielded.

    All items remain in the buffer after they are yielded, and can be yielded again, unless they
    are removed by one of the filter conditions."""
    def __init__(self, max_size, source=None, *, max_age=math.inf, min_size=1):
        super().__init__()
        self.source = source
        self.max_size = max_size
        self.max_age = max_age
        self.min_size = min_size

    async def pump(self, input, output):
        if self.source is not None:
            input = self.source
        buf = deque()
        async with aclosing(input) as aiter, output:
            async for item in aiter:
                now = trio.current_time()
                buf.append((item, now))
                while len(buf) > self.max_size or now - buf[0][1] > self.max_age:
                    buf.popleft()
                if len(buf) >= self.min_size:
                    await output.send(tuple(i[0] for i in buf))

class Group(Section):
    """Groups received items by time based interval.

    Group awaits an item to arrive from source, adds it to a buffer and sets a timeout using
    interval. While the timeout is active, additional items received are added to the buffer.
    When the timeout triggers, or if the buffer size equals max_size, the buffer is yielded and
    a new empty buffer is created.

    The buffer is not yielded at regular intervals. The timeout only starts if there are items in
    the buffer, thus the minimum length of the buffer, when it is yielded, is always 1.

    The items in the buffer can optionally be mapped over, by supplying a mapper function.

    The items can be reduced to a single value, by supplying a reducer function. Note, that the
    reducer function must take the entire buffer as a single argument and return a single value."""

    def __init__(self, interval, source=None, *,
                 max_size=math.inf,
                 mapper: Callable[[Any], Any] = None,
                 reducer: Callable[[Sequence[Any]], Any] = None):
        super().__init__()
        self.source = source
        self.interval = interval
        self.max_size = max_size
        self.mapper = mapper
        self.reducer = reducer

    async def pump(self, input, output):
        if input is None:
            if self.source is not None:
                input = self.source
            else:
                raise RuntimeError('No input provided.')
        async with output, aclosing(input) as aiter:
            while True:
                buffer = []
                try:
                    buffer.append(await aiter.__anext__())
                    with trio.move_on_after(self.interval):
                        while True:
                            if len(buffer) == self.max_size:
                                break
                            buffer.append(await aiter.__anext__())
                except StopAsyncIteration:
                    if buffer:
                        await output.send(self._process_result(buffer))
                    break
                else:
                    await output.send(self._process_result(buffer))

    def _process_result(self, buffer):
        if self.mapper is not None:
            buffer = (self.mapper(x) for x in buffer)
        if self.reducer is not None:
            return self.reducer(buffer)
        else:
            return tuple(buffer)

class Delay(Section):
    """Delays transmission of each item received by an interval.

    Received items are temporarily stored in an unbounded queue, along with a timestamp, using
    a background task. The foreground task takes items from the queue, and waits until the
    item is older than the given interval and then transmits it."""
    def __init__(self, interval: float, source=None):
        super().__init__()
        self.source = source
        self.interval = interval

    async def pump(self, input, output):
        if self.source is not None:
            input = self.source
        buffer_input_channel, buffer_output_channel = trio.open_memory_channel(math.inf)

        async def pull_task():
            async with buffer_input_channel, aclosing(input) as aiter:
                async for item in aiter:
                    await buffer_input_channel.send((item, trio.current_time() + self.interval))

        async with trio.open_nursery() as nursery:
            nursery.start_soon(pull_task)
            async with buffer_output_channel, output:
                async for item, timestamp in buffer_output_channel:
                    now = trio.current_time()
                    if timestamp > now:
                        await trio.sleep(timestamp - now)
                    await output.send(item)

class RateLimit(Section):
    """Limits data rate of an input to a certain interval.

    The first item received is transmitted and a timeout starts. Any other items received within
    interval time are discarded. When the interval is exceeded, the timeout resets and a new
    item can be transmitted."""
    def __init__(self, interval, source=None):
        super().__init__()
        self.source = source
        self.interval = interval

    async def pump(self, input, output):
        if self.source is not None:
            input = self.source
        then = 0
        async with aclosing(input) as aiter, output:
            async for item in aiter:
                now = trio.current_time()
                if now - then > self.interval:
                    then = now
                    await output.send(item)
