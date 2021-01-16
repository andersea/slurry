"""The weld module implements the ``weld`` function that connects ``PipelineSection`` objects 
together and returns the async iterable output.

A ``PipelineSection`` is any object that is valid input to the ``weld`` function. This currently
includes the following types:

* ``AsyncIterable[Any]`` - Async iterables are valid only as the very first ``PipelineSection``. Subsequent
  sections will use this async iterable as input source. Placing an ``AsyncIterable`` into the middle of
  of a sequence of pipeline sections, will cause a ``ValueError``.
* Any :class:`Section` abc subclass.
* ``Tuple[PipelineSection, ...]`` - Pipeline sections can be nested to any level by supplying a tuple
  containing one or more pipeline section-compatible objects. Output from upstream sections are
  automatically used as input to the nested sequence of pipeline sections.

The main :class:`Pipeline <slurry.Pipeline>` class uses the ``weld`` function to compose the sequence of
``PipelineSection`` objeects (see below) and return an output. Similarly, the
:ref:`combiner sections <Combining multiple inputs>` use the ``weld`` function to support defining
sub-pipelines as input sources, using the tuple notation."""

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
