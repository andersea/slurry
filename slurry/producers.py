"""Pipeline sections that produce data streams."""
from typing import Any

import trio
from async_generator import aclosing

from .abc import Section

class Repeat(Section):
    """Yields a single item repeatedly at regular intervals.

    If used as a middle section, the input can be used to set the value that is sent. When
    an input is received, it is sent immidiately, and the internal timer resets.

    :param interval: Delay between each transmission.
    :type interval: float
    :param default: Default item to send. If not supplied, will wait for an input.
    :type default: Any

    :raises RuntimeError: If used as a first section and no default is provided.
    """
    def __init__(self, interval: float, **kwargs):
        self.interval = interval
        self.kwargs = kwargs
        self.item = None
        self._item_set = trio.Event()

    async def pump(self, input, output):
        if input is None and 'default' not in self.kwargs:
            # pylint: disable=line-too-long
            raise RuntimeError('A default value must be provided, if Repeat is used as first section.')
        timer_cancel_scope = None

        async def set_item_task():
            async with aclosing(input) as aiter:
                async for item in aiter:
                    self.item = item
                    self._item_set.set()
                    if timer_cancel_scope is not None:
                        timer_cancel_scope.cancel()

        async with trio.open_nursery() as nursery:
            if input is not None:
                nursery.start_soon(set_item_task)
            if 'default' in self.kwargs:
                self.item = self.kwargs['default']
            else:
                await self._item_set.wait()
            while True:
                await output.send(self.item)
                with trio.CancelScope() as timer_cancel_scope:
                    await trio.sleep(self.interval)
