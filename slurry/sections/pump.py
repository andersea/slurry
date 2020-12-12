"""Helper functions for running sections."""
from multiprocessing import Process, SimpleQueue
from typing import Any, AsyncIterable, Awaitable, Callable, Optional

import trio

from .abc import Section, ThreadSection, ProcessSection

async def pump(section, input: Optional[AsyncIterable[Any]], output: trio.MemorySendChannel):
    """The pump function is used by the pipeline to run each section.

    Individual sections can also use this function to support running sub-sections. This is
    usually used to allow sections to be used as input, where an async iterable is normally
    expected.
    """
    try:
        if isinstance(section, Section):
            await section.pump(input, output)
        elif isinstance(section, ThreadSection):
            await _thread_section_pump(section, input, output.send)
        elif isinstance(section, ProcessSection):
            await _process_section_pump(section, input, output.send)
    except trio.BrokenResourceError:
        pass
    if input:
        await input.aclose()
    await output.aclose()

async def _thread_section_pump(section: ThreadSection,
                              input: AsyncIterable[Any],
                              output: Callable[[Any], Awaitable[None]]):
    """Runs the ThreadSection in a background thread with synchronous input and output wrappers."""

    def sync_input():
        """Wrapper for turning an async iterable into a blocking generator."""
        if input is None:
            return
        try:
            while True:
                yield trio.from_thread.run(input.__anext__)
        except StopAsyncIteration:
            pass

    await trio.to_thread.run_sync(section.pump,
                                  sync_input(),
                                  lambda item: trio.from_thread.run(output, item))

async def _process_section_pump(section: ProcessSection, input: AsyncIterable[Any], output: Callable[[Any], Awaitable[None]]):
    if input:
        input_queue = SimpleQueue()
    else:
        input_queue = None
    output_queue = SimpleQueue()
    process = Process(target=_process_section_run,
                      args=(section, input_queue, output_queue))

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

def _process_section_run(section: ProcessSection, input_queue: SimpleQueue, output_queue: SimpleQueue):
    if input_queue:
        input = (wrapped_item[0] for wrapped_item in iter(input_queue.get, ()))
    else:
        input = None
    section.pump(input, lambda item: output_queue.put((item,)))
    output_queue.put(())
