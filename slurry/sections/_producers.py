"""Pipeline sections that produce data streams."""
from time import time
from typing import Any

import trio
from async_generator import aclosing

from ..environments import TrioSection

class Repeat(TrioSection):
    """Yields a single item repeatedly at regular intervals.

    If used as a middle section, the input can be used to set the value that is sent. When
    an input is received, it is sent immidiately, and the internal timer resets.

    When an input is used, closure of the input stream will cause the repeater to close as well.

    :param interval: Delay between each transmission.
    :type interval: float
    :param default: Default item to send. If not supplied, will wait for an input.
    :type default: Any

    :raises RuntimeError: If used as a first section and no default is provided.
    """
    def __init__(self, interval: float, *args, **kwargs):
        self.interval = interval
        self.has_default = False
        self.default = None
        if args:
            self.has_default = True
            self.default = args[0]
        elif 'default' in kwargs:
            self.has_default = True
            self.default = kwargs['default']

    async def refine(self, input, output):
        if input is None and not self.has_default:
            # pylint: disable=line-too-long
            raise RuntimeError('If Repeat is used as first section,  default value must be provided.')

        async with trio.open_nursery() as nursery:

            async def repeater(item, *, task_status=trio.TASK_STATUS_IGNORED):
                with trio.CancelScope() as cancel_scope:
                    await output(item)
                    task_status.started(cancel_scope)
                    while True:
                        await trio.sleep(self.interval)
                        await output(item)

            running_repeater = None

            if self.has_default:
                running_repeater = await nursery.start(repeater, self.default)

            if input:
                async with aclosing(input) as aiter:
                    async for item in aiter:
                        if running_repeater:
                            running_repeater.cancel()
                        running_repeater = await nursery.start(repeater, item)
                nursery.cancel_scope.cancel()

class Metronome(TrioSection):
    """Yields an item repeatedly at wall clock intervals.

    If used as a middle section, the input can be used to set the value that is sent. When
    an input is received, it is stored and send at the next tick of the clock. If multiple
    inputs are received during a tick, only the latest is sent. The preceeding inputs are
    dropped.

    When an input is used, closure of the input stream will cause the metronome to close as well.

    :param interval: Wall clock delay between each transmission.
    :type interval: float
    :param default: Default item to send.
    :type default: Any

    :raises RuntimeError: If used as a first section and no default is provided.
    """
    def __init__(self, interval: float, *args, **kwargs):
        self.interval = interval
        self.has_default = False
        self.default = None
        if args:
            self.has_default = True
            self.default = args[0]
        elif 'default' in kwargs:
            self.has_default = True
            self.default = kwargs['default']

    async def refine(self, input, output):
        if input is None and not self.has_default:
            # pylint: disable=line-too-long
            raise RuntimeError('If Repeat is used as first section,  default value must be provided.')

        item = self.default if self.has_default else None

        async def pull_task(cancel_scope, *, task_status=trio.TASK_STATUS_IGNORED):
            nonlocal item
            async for item in input:
                task_status.started()
                break
            async for item in input:
                pass
            cancel_scope.cancel()

        async with trio.open_nursery() as nursery:
            if input:
                if self.has_default:
                    nursery.start_soon(pull_task, nursery.cancel_scope)
                else:
                    await nursery.start(pull_task, nursery.cancel_scope)
            while True:
                await trio.sleep(self.interval - time() % self.interval)
                await output(item)

class InsertValue(TrioSection):
    """Inserts a single user supplied value into the pipeline on startup and then
    passes through any further received items unmodified.

    :param value: Item to send on startup.
    :type value: Any
    """
    def __init__(self, value: Any) -> None:
        self.value = value

    async def refine(self, input, output):
        await output(self.value)
        async for item in input:
            await output(item)
