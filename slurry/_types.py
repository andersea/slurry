from typing import Awaitable, Protocol, runtime_checkable

@runtime_checkable
class SupportsAclose(Protocol):
    def aclose(self) -> Awaitable[object]:
        ...
