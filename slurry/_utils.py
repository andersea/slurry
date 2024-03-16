from typing import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Protocol,
    TypeVar,
    Union,
    runtime_checkable,
)

from contextlib import asynccontextmanager

_T_co = TypeVar("_T_co", covariant=True)

@asynccontextmanager
async def safe_aclosing(
        obj: Union[AsyncIterable[_T_co], AsyncIterator[_T_co]]
) -> AsyncGenerator[AsyncIterator[_T_co], None]:
    if not isinstance(obj, AsyncIterator):
        obj = obj.__aiter__()
    try:
        yield obj
    finally:
        await safe_aclose(obj)

async def safe_aclose(obj: AsyncIterator[_T_co]) -> None:
    if isinstance(obj, _SupportsAclose):
        await obj.aclose()

@runtime_checkable
class _SupportsAclose(Protocol):
    def aclose(self) -> Awaitable[object]:
        ...
