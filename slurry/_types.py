from typing import Any, AsyncIterable, Awaitable, Protocol, Tuple, Union, runtime_checkable

from .sections.abc import Section

PipelineSection = Union[AsyncIterable[Any], Section, Tuple["PipelineSection", ...]]

@runtime_checkable
class SupportsAclose(Protocol):
    def aclose(self) -> Awaitable[object]:
        ...
