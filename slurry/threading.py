"""Helpers for running threaded sections"""

from typing import Any, AsyncIterable
import trio

from .abc import SyncSendObject

def sync_input(input: AsyncIterable[Any]):
    """Wrapper for turning an async iterable into a blocking generator."""
    if input is None:
        return
    try:
        while True:
            item = trio.from_thread.run(input.__anext__)
            yield item
    except StopAsyncIteration:
        pass

def sync_output(output: trio.MemorySendChannel):
    """Wraps the async send function of a trio MemorySendChannel in a blocking
    synchronous interface."""
    return _SyncMemorySendChannelWrapper(output)

class _SyncMemorySendChannelWrapper(SyncSendObject):
    """Synchronous blocking MemorySendChannel interface."""
    def __init__(self, output: trio.MemorySendChannel) -> None:
        self._output = output

    def send(self, item: Any) -> None:
        """Blocking MemorySendChannel.send() wrapper."""
        trio.from_thread.run(self._output.send, item)
