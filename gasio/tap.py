import trio

class Tap:
    def __init__(self, send_channel, timeout, retrys):
        self.send_channel = send_channel
        self.timeout = timeout
        self.retrys = retrys

    async def send(self, item):
        for _ in range(self.retrys + 1):
            with trio.move_on_after(self.timeout):
                await self.send_channel.send(item)
                return
            await trio.sleep(0)
        raise trio.BusyResourceError('Unable to send item.')
