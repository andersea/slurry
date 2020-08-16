"""Pipeline output tap."""
import trio

class Tap:
    """The tap class is responsible for transmitting the output of the pipeline to consumers.
    It implements an asynchronous send function that is launched as a task from the pipeline for
    each item processed. Each tap can be individually configured with send timeouts and retry
    attempts.
    """
    def __init__(self, send_channel, timeout, retrys):
        self.send_channel = send_channel
        self.timeout = timeout
        self.retrys = retrys

    async def send(self, item):
        """Handles the transmission of a single item from the pipeline.

        Each send operation is run as a task, so that in case of multiple consumers, a stuck
        consumer won't block the entire send loop.
        """
        for _ in range(self.retrys + 1):
            with trio.move_on_after(self.timeout):
                await self.send_channel.send(item)
                return
            await trio.sleep(0)
        raise trio.BusyResourceError('Unable to send item.')
