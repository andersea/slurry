from itertools import chain
from typing import Any, AsyncIterable, Sequence, Union

import trio

from .abc import Section, ThreadSection, ProcessSection
from .pump import pump

def weld(
    nursery,
    *sections: Sequence[Union[AsyncIterable[Any], Section, ThreadSection, ProcessSection]]
    ) -> AsyncIterable[Any]:

    section_input = None
    output = None
    for section in sections:
        if isinstance(section, (Section, ThreadSection, ProcessSection)):
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
