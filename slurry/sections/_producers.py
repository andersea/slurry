"""Pipeline sections that produce data streams."""
import trio
from async_generator import aclosing

from ..environments import TrioSection

class Repeat(TrioSection):
    """Yields a single item repeatedly at regular intervals.

    If used as a middle section, the input can be used to set the value that is sent. When
    an input is received, it is sent immidiately, and the internal timer resets.

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
