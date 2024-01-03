from typing import AsyncGenerator, AsyncIterator, TypeVar

from ._types import SupportsAclose

from contextlib import asynccontextmanager

_T = TypeVar("_T")

@asynccontextmanager
async def safe_aclosing(obj: AsyncIterator[_T]) -> AsyncGenerator[AsyncIterator[_T], None]:
    try:
        yield obj
    finally:
        if isinstance(obj, SupportsAclose):
            await obj.aclose()
