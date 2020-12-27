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

            def start_new_repeater(item):
                cancel_scope = trio.CancelScope()
                async def repeater():
                    with cancel_scope:
                        while True:
                            await trio.sleep(self.interval)
                            await output(item)                
                nursery.start_soon(repeater)
                return cancel_scope

            previous_repeater = None

            if self.has_default:
                await output(self.default)
                previous_repeater = start_new_repeater(self.default)

            if input:
                async with aclosing(input) as aiter:
                    async for item in aiter:
                        if previous_repeater:
                            previous_repeater.cancel()
                        await output(item)
                        previous_repeater = start_new_repeater(item)
