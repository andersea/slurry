"""The threading module implements a synchronous section that runs in a background thread."""
from typing import Any, AsyncIterable, Awaitable, Callable

import trio

from .abc import SyncSection


class ThreadSection(SyncSection):
    """ThreadSection defines a section interface which uses a synchronous refine method.
    The refine method runs in a background thread and will not block the underlying
    event loop.

    See :class:`slurry.sections.abc.SyncSection` for more information.
    """

    async def pump(self,
                   input: AsyncIterable[Any],
                   output: Callable[[Any], Awaitable[None]]):
        """Runs the ThreadSection in a background thread with synchronous input and output
        wrappers, which transparently bridges the input and outputs between the parent
        trio event loop and the sync world.

        .. note::
            Trio has a limit on how many threads can run simultaneously. See the
            `trio documentation <https://trio.readthedocs.io/en/stable/reference-core.html#trio-s-philosophy-about-managing-worker-threads>`_
            for more information.
        """

        def sync_input():
            """Wrapper for turning an async iterable into a blocking generator."""
            if input is None:
                return
            try:
                while True:
                    yield trio.from_thread.run(input.__anext__)
            except StopAsyncIteration:
                pass

        await trio.to_thread.run_sync(self.refine,
                                      sync_input(),
                                      lambda item: trio.from_thread.run(output, item))
