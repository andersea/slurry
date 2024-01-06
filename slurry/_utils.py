from typing import AsyncGenerator, TypeVar

from ._types import AcloseableAsyncIterator

from contextlib import asynccontextmanager

_T = TypeVar("_T")

@asynccontextmanager
async def aclosing(obj: AcloseableAsyncIterator[_T]) -> AsyncGenerator[AcloseableAsyncIterator[_T], None]:
    try:
        yield obj
    finally:
        await obj.aclose()
