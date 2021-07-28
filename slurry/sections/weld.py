"""Contains the `weld` utility function for composing sections."""

from typing import Any, AsyncIterable, Optional, Sequence

import trio

from .abc import Section

def weld(nursery, *sections: Sequence["PipelineSection"]) -> AsyncIterable[Any]:
    """
    Connects the individual parts of a sequence of pipeline sections together and starts pumps for
    individual Sections. It returns an async iterable which yields results of the sequence.

    :param nursery: The nursery that runs individual pipeline section pumps.
    :type nursery: :class:`trio.Nursery`
    :param \\*sections: A sequence of pipeline sections.
    :type \\*sections: Sequence[PipelineSection]
    """

    async def pump(section, input: Optional[AsyncIterable[Any]], output: trio.MemorySendChannel):
        try:
            await section.pump(input, output.send)
        except trio.BrokenResourceError:
            pass
        if input:
            await input.aclose()
        await output.aclose()

    section_input = None
    output = None
    for section in sections:
        if isinstance(section, Section):
            section_output, output = trio.open_memory_channel(0)
            nursery.start_soon(pump, section, section_input, section_output)
        elif isinstance(section, tuple):
            if section_input:
                output = weld(nursery, section_input, *section)
            else:
                output = weld(nursery, *section)
        else:
            if output:
                raise ValueError('Invalid pipeline section.', section)
            output = section
        section_input = output

    return output
