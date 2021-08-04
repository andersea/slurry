"""Implements a section that runs in an independent python proces."""

from multiprocessing import Process, SimpleQueue
from typing import Any, Iterable, Callable

import trio

from ..sections.abc import SyncSection

class ProcessSection(SyncSection):
    """ProcessSection defines a section interface with a synchronous
    :meth:`refine <slurry.sections.abc.SyncSection.refine>` method that
    runs in a separate process. Slurry makes use of the python
    `multiprocessing <https://docs.python.org/3/library/multiprocessing.html>`_ module
    to spawn the process.

    .. note::
        ``ProcessSection`` implementations must be `pickleable
        <https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled>`_.
    """

    async def pump(self, input: Iterable[Any], output: Callable[[Any], None]):
        """
        The ``ProcessSection`` pump method works similar to the threaded version, however
        since communication between processes is not as simple as it is between threads,
        that are directly able to share memory with each other, there are some restrictions
        to be aware of.

        * Data that is to be sent to the input or transmitted on the output must be `pickleable
          <https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled>`_.
        * Since ``ProcessSection`` uses unbounded queues to transfer data behind the scenes, they
          are unable to provide or receive backpressure.
        """
        if input:
            input_queue = SimpleQueue()
        else:
            input_queue = None
        output_queue = SimpleQueue()
        process = Process(target=self._process_run_target,
                          args=(input_queue, output_queue))

        async def sender():
            async for item in input:
                await trio.to_thread.run_sync(input_queue.put, (item,))
            await trio.to_thread.run_sync(input_queue.put, ())

        async with trio.open_nursery() as nursery:
            if input:
                nursery.start_soon(sender)
            process.start()
            while True:
                wrapped_item = await trio.to_thread.run_sync(output_queue.get)
                if wrapped_item == ():
                    break
                await output(wrapped_item[0])
            nursery.cancel_scope.cancel()

    def _process_run_target(self, input_queue: SimpleQueue, output_queue: SimpleQueue):
        if input_queue:
            input = (wrapped_item[0] for wrapped_item in iter(input_queue.get, ()))
        else:
            input = None
        self.refine(input, lambda item: output_queue.put((item,)))
        output_queue.put(())
